#!/usr/bin/env python3
"""
VibeCoding Athena v9.7.0 · Codex Stop hook (delivery-gate)

触发: 主 thread stop
职责:
1. Refactor/System ship → 必须有 cleanup-pass.md
2. Feature/Refactor/System ship → pass1.md 含 '## Spec Compliance' 段
3. Refactor/System (≥5 文件) ship → architecture/ 必须存在 (铁律[架构])
4. design_changed_after_impl=true + ship → block (要重新 review)
5. current_roadmap_slug 非空 + items.yaml 还有 pending → 提醒 (不 block)
6. stage 合规性检查

v9.7.0 修正:
- [官方 developers.openai.com/codex/hooks] Stop 事件要求 JSON 输出
  (plain text 无效); block 统一为 exit 0 + {"decision":"block","reason":...}
- F1 修复: 文件变更数原先只读 evidence.yaml, 但 CX 端无文件写 hook →
  evidence.yaml 无 file 记录 → 架构门禁永不触发 (死门禁).
  现在优先用 git diff --stat 现场计算, evidence.yaml 为辅 (取大者).
- block reason 必须含明确解锁动作
"""
import json
import re
import subprocess
import sys
from pathlib import Path

EXIT_SUCCESS = 0

REFACTOR_SYSTEM = {"Refactor", "System"}
VALID_STAGES = {"brainstorm", "roadmap", "plan", "design", "impl", "review", "polish", "ship"}


def find_ai_state(cwd: Path):
    current = cwd
    for _ in range(5):
        candidate = current / ".ai_state"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            return None
        current = current.parent
    return None


def parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm: dict = {}
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


def block(reason: str) -> int:
    """官方 CX Stop 协议: JSON stdout, decision block + reason 生成续跑提示.
    exit 0 (结构化控制走 JSON, 不混用 exit 2)."""
    sys.stderr.write(reason + "\n")
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return EXIT_SUCCESS


def count_changed_files_git(cwd: Path) -> int:
    """v9.7.0 主路径: git diff 现场计算本分支变更文件数 (修 F1 死门禁)."""
    for base in ("main...HEAD", "master...HEAD"):
        try:
            r = subprocess.run(
                ["git", "diff", "--name-only", base],
                cwd=str(cwd), capture_output=True, text=True, timeout=15,
            )
            if r.returncode == 0:
                files = [ln for ln in r.stdout.splitlines() if ln.strip()]
                if files:
                    return len(files)
        except Exception:
            pass
    return 0


def count_changed_files_evidence(ai_state: Path, sprint_slug: str) -> int:
    """辅路径: evidence.yaml 的 file 字段去重计数 (CX 过程证据中 file 多为空)."""
    evidence = ai_state / "sprints" / sprint_slug / "evidence.yaml"
    if not evidence.exists():
        return 0
    files = set()
    for line in evidence.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"\s*file:\s*[\"']?([^\"\n]+)[\"']?", line)
        if m and m.group(1).strip():
            files.add(m.group(1).strip())
    return len(files)


def has_pending_roadmap_items(items_yaml: Path) -> bool:
    if not items_yaml.exists():
        return False
    return "status: pending" in items_yaml.read_text(encoding="utf-8")


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}

        cwd = Path.cwd()
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            return EXIT_SUCCESS

        idx = ai_state / "_index.md"
        if not idx.exists():
            return EXIT_SUCCESS

        content = idx.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)

        path = fm.get("path", "")
        stage = fm.get("stage", "")
        sprint_slug = fm.get("current_sprint_slug", "")
        roadmap_slug = fm.get("current_roadmap_slug", "")
        design_changed = fm.get("design_changed_after_impl", "false").lower() == "true"
        skip_arch = fm.get("skip_architecture_check", "false").lower() == "true"

        # ============ ship 前 spec-compliance 门禁 ============
        # 后台架构: review agent 后台跑, 主 agent 监控到完成才推进 stage=ship.
        # review 阶段不设同步门 (会死锁); 门禁统一在 ship (产物已落盘).
        if path in ("Feature", "Refactor", "System") and stage == "ship" and sprint_slug:
            pass1 = ai_state / "sprints" / sprint_slug / "reviews" / "pass1.md"
            if not pass1.exists():
                return block(
                    f"[delivery-gate] {path} 路径 ship 前必须完成 review.\n"
                    "解锁动作: 等后台 review agent 写完 reviews/pass1.md 再推进 stage=ship; "
                    "未跑 review 则先 spawn reviewer + spec-compliance + evaluator.\n"
                )
            if "## Spec Compliance" not in pass1.read_text(encoding="utf-8"):
                return block(
                    "[delivery-gate] pass1.md 缺 '## Spec Compliance' 段.\n"
                    "解锁动作: spawn_agent spec-compliance.toml 补齐该段后再 ship.\n"
                )

        # ============ design_changed_after_impl + ship → block ============
        if design_changed and stage == "ship":
            return block(
                "[delivery-gate] design.md 在 impl/review/polish 后被修改, ship 前必须重新 review.\n"
                "解锁动作: spawn_agent reviewer.toml + spec-compliance.toml + evaluator.toml, "
                "然后设 _index.md.design_changed_after_impl = false 再 ship.\n"
            )

        # ============ roadmap 未完提醒 (不 block) ============
        if roadmap_slug and stage == "ship":
            items_yaml = ai_state / "roadmap" / roadmap_slug / "items.yaml"
            if has_pending_roadmap_items(items_yaml):
                sys.stderr.write(
                    f"[delivery-gate] 提醒: roadmap {roadmap_slug} 还有 pending items, "
                    f"本 sprint ship 后, 主 agent 应继续下个 item.\n"
                )

        # ============ Refactor/System ship → 必须有 cleanup-pass ============
        if path in REFACTOR_SYSTEM and stage == "ship":
            cleanup_file = ai_state / "sprints" / sprint_slug / "cleanup-pass.md"
            old_cleanup = ai_state / "details" / "cleanup-pass.md"  # 兼容 v9.6.2 老路径
            if not cleanup_file.exists() and not old_cleanup.exists():
                return block(
                    "[delivery-gate] Refactor/System 路径必须先完成 polish stage.\n"
                    f"解锁动作: 运行 /polish 生成 sprints/{sprint_slug}/cleanup-pass.md\n"
                )

        # ============ Refactor/System (≥5 文件) ship → architecture 必须存在 (铁律[架构]) ============
        if path in REFACTOR_SYSTEM and stage == "ship" and not skip_arch:
            changed = max(
                count_changed_files_git(cwd),
                count_changed_files_evidence(ai_state, sprint_slug) if sprint_slug else 0,
            )
            if changed >= 5:
                arch_dir = ai_state / "architecture"
                if not arch_dir.exists():
                    return block(
                        "[delivery-gate] 铁律[架构]: Refactor/System 路径 ship 前必须更新 architecture/ 现状档.\n"
                        f"本 sprint 改了 {changed} 个文件, architecture/ 目录不存在.\n"
                        "解锁动作: 运行 /architect-doc update 生成或刷新.\n"
                        "(若不需要, 在 _index.md 设 skip_architecture_check: true 跳过, 但不推荐)\n"
                    )
                arch_files = list(arch_dir.glob("**/*.md"))
                if not arch_files:
                    return block(
                        "[delivery-gate] architecture/ 目录存在但无 .md 文件.\n"
                        "解锁动作: 运行 /architect-doc update.\n"
                    )
                # 简化: 不严格比 sprint 开始时间, 只确保有 architecture 文件 (避免 mtime 误判)

        # ============ stage 合规性 (8 stage) ============
        if stage and stage not in VALID_STAGES:
            sys.stderr.write(
                f"[delivery-gate] warning: 未知 stage '{stage}', 期望 {VALID_STAGES}\n"
            )

        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[delivery-gate] warning (non-blocking): {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
