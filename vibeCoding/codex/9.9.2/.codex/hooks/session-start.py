#!/usr/bin/env python3
"""
VibeCoding Athena v9.9.2 · Codex SessionStart hook

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
            k, v = m.group(1), m.group(2).strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            fm[k] = v
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
        if len(content) > 600:
            content = content[:600] + f"\n... (see {label}/ for full)"
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


def main() -> int:
    try:
        cwd = Path.cwd()
        ai_state = find_ai_state(cwd)

        context_parts = []

        if ai_state:
            idx_path = ai_state / "_index.md"
            summary = read_frontmatter_summary(idx_path)
            if summary:
                context_parts.append(f"## Athena 项目状态 (.ai_state/_index.md)\n\n{summary}")

            fm = parse_frontmatter(idx_path)

            alerts = special_alerts(fm)
            if alerts:
                context_parts.append("## 🚨 重要提醒\n\n" + "\n\n".join(alerts))

            hints = stage_hints(fm)
            if hints:
                context_parts.append(
                    f"## 当前 stage 操作提示 (stage: {fm.get('stage') or 'unknown'})\n\n"
                    + "\n".join(hints)
                )

            # v9.8.0: 主动提醒会话记忆固化 (athena-checkpoint 的触达半径)
            context_parts.append(
                "## 💾 会话记忆 (v9.8.0)\n\n长任务收尾 / context 快满 / 关键决策后, 跑 "
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
