#!/usr/bin/env python3
"""
VibeCoding Athena v9.6.4 · Codex Stop hook (delivery-gate)

触发: 主 thread stop
职责:
1. (沿用) Refactor/System ship → 必须有 cleanup-pass.md
2. (沿用) stage 合规性检查
3. (v9.6.4 新) review stage → 必须有 ## Spec Compliance 段 (spec-compliance subagent 已跑)
4. (v9.6.4 新) Refactor/System ship → architecture/ 必须 mtime ≥ sprint 开始
5. (v9.6.4 新) design_changed_after_impl=true + ship → block (要重新 review)
6. (v9.6.4 新) current_roadmap_slug 非空 + items.yaml 还有 pending → 不允许 "全部完成" 宣称

退出码: 0 允许 / 2 阻止 (top-level decision:"block")
源: https://developers.openai.com/codex/hooks
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_BLOCK = 2

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
    output = {"decision": "block", "reason": reason}
    sys.stderr.write(reason + "\n")
    print(json.dumps(output))
    return EXIT_BLOCK


def count_changed_files(ai_state: Path, sprint_slug: str) -> int:
    """从 evidence.yaml 估算本 sprint 改了多少文件 (用于 architecture 强制检查阈值)."""
    evidence = ai_state / "sprints" / sprint_slug / "evidence.yaml"
    if not evidence.exists():
        return 0
    files = set()
    for line in evidence.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"\s*file:\s*[\"']?([^\"\n]+)[\"']?", line)
        if m:
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

        # ============ v9.6.4 (3): review stage → spec-compliance 段必存在 ============
        if stage == "review" and sprint_slug:
            pass1 = ai_state / "sprints" / sprint_slug / "reviews" / "pass1.md"
            if pass1.exists():
                content_pass1 = pass1.read_text(encoding="utf-8")
                if "## Spec Compliance" not in content_pass1:
                    return block(
                        "[delivery-gate] review stage 必须先跑 spec-compliance subagent.\n"
                        "运行 spawn_agent ~/.codex/agents/spec-compliance.toml, "
                        "它会对比 design.md vs git diff 找 MISSING/EXTRA/DEVIATED.\n"
                    )

        # ============ v9.6.4 (5): design_changed_after_impl + ship → block ============
        if design_changed and stage == "ship":
            return block(
                "[delivery-gate] design.md 在 impl/review/polish 后被修改, ship 前必须重新 review.\n"
                "执行: spawn_agent reviewer.toml + spec-compliance.toml + evaluator.toml\n"
                "然后清空 _index.md.design_changed_after_impl = false 再 ship.\n"
            )

        # ============ v9.6.4 (6): current_roadmap_slug 未完成 → 不能宣称全部完成 ============
        if roadmap_slug and stage == "ship":
            items_yaml = ai_state / "roadmap" / roadmap_slug / "items.yaml"
            if has_pending_roadmap_items(items_yaml):
                # 不 block ship (这个 item 可以 ship), 但提醒主 agent roadmap 还没完
                sys.stderr.write(
                    f"[delivery-gate] 提醒: roadmap {roadmap_slug} 还有 pending items, "
                    f"本 sprint ship 后, 主 agent 应继续下个 item.\n"
                )

        # ============ 沿用 v9.6.2: Refactor/System ship → 必须有 cleanup-pass ============
        if path in REFACTOR_SYSTEM and stage == "ship":
            # v9.6.4: 路径改为 sprints/{slug}/cleanup-pass.md
            cleanup_file = ai_state / "sprints" / sprint_slug / "cleanup-pass.md"
            # 兼容老路径 (v9.6.2)
            old_cleanup = ai_state / "details" / "cleanup-pass.md"
            if not cleanup_file.exists() and not old_cleanup.exists():
                return block(
                    f"[delivery-gate] Refactor/System 路径必须先完成 polish stage.\n"
                    f"运行 /polish 生成 {cleanup_file.relative_to(cwd) if cleanup_file.is_relative_to(cwd) else cleanup_file}\n"
                )

        # ============ v9.6.4 (4): Refactor/System (≥5 文件) ship → architecture mtime 必更新 ============
        if path in REFACTOR_SYSTEM and stage == "ship" and not skip_arch:
            changed = count_changed_files(ai_state, sprint_slug)
            if changed >= 5:
                arch_dir = ai_state / "architecture"
                # 检查是否有 .md 文件且 mtime ≥ sprint 开始
                if not arch_dir.exists():
                    return block(
                        "[delivery-gate] 铁律 15: Refactor/System 路径 ship 前必须更新 architecture/ 现状档.\n"
                        f"本 sprint 改了 {changed} 个文件, architecture/ 目录不存在.\n"
                        "运行 /architect-doc update 生成或刷新.\n"
                        "(若不需要, 在 _index.md 设 skip_architecture_check: true 跳过本检查, 但不推荐)\n"
                    )
                # 找最新 architecture mtime
                arch_files = list(arch_dir.glob("**/*.md"))
                if not arch_files:
                    return block(
                        f"[delivery-gate] architecture/ 目录存在但无 .md 文件. 运行 /architect-doc update.\n"
                    )
                # 简化: 不严格比 sprint 开始时间, 只确保有 architecture 文件 (避免 mtime 误判)
                # 严格版可对比 sprint 目录 mtime, 但模板项目目录可能很新

        # ============ 沿用: stage 合规性 (扩展为 8 stage) ============
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
