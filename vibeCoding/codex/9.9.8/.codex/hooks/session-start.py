#!/usr/bin/env python3
"""
VibeCoding Athena v9.9.6 · Codex SessionStart hook

触发: session 启动 / resume / clear
职责:
1. 注入 _index.md frontmatter 摘要
2. 注入 ~/.codex/standards/_index.md 摘要 (兼容旧 ~/.agents/standards)
3. stage-specific 操作提示 (xhigh / critic / spec-compliance)
4. design_changed_after_impl=true 强提示
5. next_action = roadmap 自动推进提示

v9.7.0: impl 提示与铁律[零写入]红黄绿区同步 (绿区主 thread 直做)
源: https://developers.openai.com/codex/hooks
"""
import json
import os
import re
import sys
from pathlib import Path

EXIT_SUCCESS = 0
POINTER_KEYS = ("latest_design", "latest_review", "latest_cleanup", "latest_requirement")


# v9.9.6: SessionStart 只注入路由必需字段.
INDEX_CORE = ("version", "path", "stage", "current_sprint_slug", "current_roadmap_slug",
              "next_action", "plan_model", "platforms_enabled")
INDEX_SKIP_FLAGS = ("skip_polish", "skip_architecture_check", "skip_runtime_verify")
# latest_design/review/cleanup/requirement 由 memory router 注入, 此处不重复
INDEX_POINTERS = ("latest_decisions", "latest_lessons")



def pending_escalation(ai_state, sprint_slug):
    """hotfix2 (2026-07-29, W39): 与 CC 语义对齐 — 尾部 GateEscalated 且其后无 GatePass
    = 升级未消解, SessionStart 必须告警 (熔断不是放行)。fail-open。"""
    if not sprint_slug:
        return None
    try:
        import json as _json
        rows = []
        for line in (ai_state / "sprints" / sprint_slug / "stop-failures.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = _json.loads(line)
                if isinstance(row, dict) and row.get("event") in ("GateBlock", "GateEscalated", "GatePass"):
                    rows.append(row)
            except ValueError:
                continue
        last = rows[-1] if rows else None
        return last if last and last.get("event") == "GateEscalated" else None
    except Exception:
        return None


def render_index_whitelist(fm: dict) -> str:
    lines = [f"{k}: {str(fm.get(k) or '').strip()}" for k in INDEX_CORE if str(fm.get(k) or "").strip()]
    lines += [f"{k}: true" for k in INDEX_SKIP_FLAGS if str(fm.get(k) or "").strip() == "true"]
    ptr = []
    for k in INDEX_POINTERS:
        raw = str(fm.get(k) or "").strip()
        if not raw:
            continue
        items = [s.strip().strip('"') for s in raw.strip("[]").split(",") if s.strip()]
        if not items:
            continue
        extra = f" (+{len(items) - 1} more, 见 _index)" if len(items) > 1 else ""
        ptr.append(f"{k}: {items[0]}{extra}")
    if ptr:
        lines.append("# pointers"); lines += ptr
    if not lines:
        return ""
    return "\n".join(lines) + "\n\n其余字段按需读 .ai_state/_index.md (历史/统计/能力探测不自动注入)."


def find_ai_state(cwd: Path):
    for _ in range(5):
        if (cwd / ".ai_state").is_dir():
            return cwd / ".ai_state"
        if cwd.parent == cwd:
            return None
        cwd = cwd.parent
    return None


def read_frontmatter_summary(idx_path: Path) -> str:
    if not idx_path.exists():
        return ""
    content = idx_path.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[1].strip()
    return ""


def strip_inline_comment(value: str) -> str:
    """与 CC parseFrontmatter 对齐: 取首对引号内的值, 否则剥 ' #' 之后的行尾注释."""
    value = value.strip()
    q = re.match(r'^"([^"]*)"|^\'([^\']*)\'', value)
    if q:
        return q.group(1) if q.group(1) is not None else q.group(2)
    idx = value.find(" #")
    return value[:idx].strip() if idx >= 0 else value


def parse_frontmatter(idx_path: Path) -> dict:
    if not idx_path.exists():
        return {}
    content = idx_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([\w\-_.]+)\s*:\s*(.*)$", line)
        if m:
            fm[m.group(1)] = strip_inline_comment(m.group(2))
    return fm


def read_standards_summary() -> tuple[str, str]:
    home = Path.home()
    candidates = [
        (home / ".codex" / "standards" / "_index.md", "~/.codex/standards"),
        (home / ".agents" / "standards" / "_index.md", "~/.agents/standards"),
    ]
    for idx, label in candidates:
        if not idx.exists():
            continue
        content = idx.read_text(encoding="utf-8")
        raw = content.encode("utf-8")
        if len(raw) > 600:
            content = raw[:600].decode("utf-8", "ignore") + f"\n... (see {label}/ for full)"
        return content, label
    return "", ""


def stage_hints(fm: dict) -> list:
    stage = fm.get("stage", "")
    hints = []

    if stage in ("plan", "design"):
        hints.append("🧠 **plan/design stage**: Codex `plan_mode_reasoning_effort = xhigh` 已生效 (config.toml).")
        hints.append("🔍 完成 design.md `## Round N` 后, 用原生 spawn_agent 启动 critic; critic 只返回 findings, 主 thread 落盘.")
        max_rounds = fm.get("plan_critique_max_rounds", "4")
        last_round = fm.get("last_critic_round", "0")
        hints.append(f"📊 critic 多轮限制: max={max_rounds}, 已跑={last_round}.")

    if stage == "impl":
        hints.append("🔧 **impl stage**: 铁律[零写入] 按区路由 —")
        hints.append("   - 绿区 (单文件 ≤30 行无跨模块影响, 或 Hotfix/Quick): 主 thread 直接做")
        hints.append("   - 黄区 (单模块): 原生 spawn_agent 分派 generator, message 写明唯一写集")
        path_type = fm.get("path", "")
        if path_type in ("Refactor", "System"):
            hints.append(f"⚠️ path={path_type} (红区): 主 thread 先创建 worktree; 分派 message 传绝对路径, 执行命令显式设 workdir 并先 pwd.")
        else:
            hints.append("   - 红区 (Refactor/System / 并行 ≥2 写者): 主 thread 先建 worktree, 再用原生 spawn_agent 分派绝对路径")

    if stage == "runtime-verify":
        hints.append("🔁 **runtime-verify stage** (v9.8.0, System/Refactor 强制): 运行时自测自改环.")
        hints.append("   - 跑 /athena-runtime-verify, 用 Codex Goals 承载: 实跑接口 + 模拟数据(正常/边界/异常) + 自测自改")
        hints.append('   - ⚠️ 完成判定只看对话里展示的: 完成条件写成"把实跑命令+输出晒进对话"')
        hints.append('   - 出口 reflect: 列"还有哪里没完善" → 回 impl 补 或 next_action=review')

    if stage == "review":
        hints.append("🔎 **review stage**: 原生 spawn_agent 并行分派 reviewer + spec-compliance; 两者只返回 findings.")
        hints.append("   - 主 thread 合并 pass1.md, 再分派 evaluator 返回最终 VERDICT")
        hints.append("   - 所有 .ai_state 写入与 stage 转换由主 thread 执行")

    if stage == "polish":
        hints.append("✨ **polish stage** (Refactor/System 强制):")
        hints.append("   - 用原生 spawn_agent 分派 polish_worker; 主 thread 合并其结果")
        hints.append("   - 5 检查项 + worktree 清理 (borrowed: Superpowers finishing-a-development-branch)")

    return hints


def special_alerts(fm: dict) -> list:
    alerts = []

    if fm.get("design_changed_after_impl", "false").lower() == "true":
        alerts.append("🚨 **design 改后未重新 review**: ship 前必须重新跑 reviewer + spec-compliance + evaluator. delivery-gate 会 block.")

    next_action = fm.get("next_action", "")
    if next_action.startswith("next_roadmap_item:"):
        slug = next_action.split(":", 1)[1]
        alerts.append(f"🎯 **roadmap 推进**: 上 sprint 完成, 自动进入下一 item \"{slug}\". 进 plan stage 处理.")
    elif next_action == "roadmap_complete":
        alerts.append("🎉 **roadmap 完成**: 所有 items 已 ship, 触发 /compound add learning 沉淀经验.")

    active_wts = fm.get("active_worktrees", "[]")
    if active_wts != "[]":
        alerts.append(f"🌿 **活着的 worktree**: {active_wts}. 检查 sprints/{{current_sprint}}/worktrees.yaml.")

    return alerts


def memory_router_context(ai_state: Path, idx_path: Path, fm: dict) -> str:
    lines = [
        "Tier1 working memory is non-authoritative conversation/tool context.",
        "Tier2 persistent memory is the versioned .ai_state project truth.",
        "_index.md retrieval router is bounded routing metadata, not a second database.",
    ]
    current_sprint = fm.get("current_sprint_slug", "")
    for key in POINTER_KEYS:
        if key not in fm:
            lines.append(f"⚠ malformed router: missing required pointer key {key}")
            continue
        value = fm.get(key, "").strip()
        if not value:
            continue
        target = (ai_state / value).resolve()
        try:
            target.relative_to(ai_state.resolve())
        except ValueError:
            lines.append(f"⚠ escaping authoritative pointer {key}: {value}")
            continue
        if not target.is_file():
            lines.append(f"⚠ missing authoritative pointer {key}: {value}")
            continue
        lines.append(f"✓ routed {key}: {value}")
        if key == "latest_review" and current_sprint:
            reviews = ai_state / "sprints" / current_sprint / "reviews"
            numbered = []
            if reviews.is_dir():
                for candidate in reviews.glob("pass*.md"):
                    match = re.fullmatch(r"pass([1-9]\d*)\.md", candidate.name)
                    if match:
                        numbered.append((int(match.group(1)), candidate.resolve()))
            if numbered and target != max(numbered, key=lambda item: item[0])[1]:
                lines.append(f"⚠ stale authoritative pointer {key}: {value}")

    route_history = fm.get("route_history", "[]").strip()
    if not (route_history.startswith("[") and route_history.endswith("]")):
        lines.append("⚠ malformed route_history: expected inline list capped at 10")
    else:
        inner = route_history[1:-1].strip()
        count = inline_list_count(inner)
        if count > 10:
            lines.append(f"⚠ route_history overflow: {count} entries (max 10)")

    content = idx_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"(?ms)^## 当前状态\s*$\n(.*?)(?=^##\s|\Z)", content)
    if match:
        entries = re.findall(r"(?m)^###\s+|^\s*-\s+", match.group(1))
        if len(entries) > 10:
            lines.append(f"⚠ current-state log overflow: {len(entries)} entries (max 10)")
    return "\n".join(lines)


def inline_list_count(inner: str) -> int:
    if not inner:
        return 0
    count, quote, escaped = 1, "", False
    for char in inner:
        if escaped:
            escaped = False
        elif char == "\\" and quote == '"':
            escaped = True
        elif quote:
            if char == quote:
                quote = ""
        elif char in {'"', "'"}:
            quote = char
        elif char == ",":
            count += 1
    return count


def main() -> int:
    try:
        cwd = Path.cwd()
        ai_state = find_ai_state(cwd)

        context_parts = []


        if ai_state:
            idx_path = ai_state / "_index.md"
            fm = parse_frontmatter(idx_path)

            # hotfix2 W39: 未消解 GateEscalated 必须在 SessionStart 告警 (与 CC 对齐)
            esc = pending_escalation(ai_state, fm.get("current_sprint_slug", ""))
            if esc:
                context_parts.append(
                    "## 🛑 门禁升级未消解\n\n上次 Stop 连续 %s 次同因阻断后熔断 (ESCALATED, %s)。"
                    "阻断未解除, 只是停止空转; 查 stop-failures.jsonl 修根因, 不得当作已通过。"
                    % (esc.get("consecutive", "?"), esc.get("ts", "?"))
                )
            summary = render_index_whitelist(fm)
            if summary:
                context_parts.append(f"## Athena 项目状态 (.ai_state/_index.md)\n\n{summary}")

            context_parts.append("## Two-tier memory retrieval\n\n" + memory_router_context(ai_state, idx_path, fm))

            alerts = special_alerts(fm)
            if alerts:
                context_parts.append("## 🚨 重要提醒\n\n" + "\n\n".join(alerts))

            # v9.9.6: stage 操作提示移交 user-prompt-submit.py 每轮注入 (与 CC 9.9.3 同构,
            # 单一真相在 skills/pace/references/stages.md). SessionStart 不再重复一份.

            # Tier1 is never elevated over Tier2; checkpoint writes durable
            # decisions/state before compaction or handoff.
            context_parts.append(
                "## 💾 会话记忆 (v9.9.6)\n\n长任务收尾 / context 快满 / 关键决策后, 跑 "
                "`/athena-checkpoint` 把进展固化进 .ai_state (免每次手动描述). 与 PreCompact 兜底互补."
            )

        standards, standards_path = read_standards_summary()
        if standards:
            context_parts.append(f"## 项目规范摘要 ({standards_path}/_index.md)\n\n{standards}")

        if context_parts:
            # Codex SessionStart 协议: stdout 即注入 context
            print("\n\n---\n\n".join(context_parts))

        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[session-start] warning (non-blocking): {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
