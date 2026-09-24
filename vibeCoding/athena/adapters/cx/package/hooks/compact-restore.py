#!/usr/bin/env python3
"""
VibeCoding Athena v9.9.6 · Codex PostCompact hook

职责: compact 后注入 .ai_state/_index.md frontmatter 摘要到 additionalContext (恢复 state 感知)
协议 [官方 developers.openai.com/codex/hooks]:
  additionalContext 放 hookSpecificOutput 并带 hookEventName
逻辑对齐 CC 端 compact-restore.cjs. 非阻塞.
"""
import json
import sys
from pathlib import Path


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


def main() -> int:
    try:
        ai_state = find_ai_state(Path.cwd())
        if ai_state is None:
            return 0
        idx = ai_state / "_index.md"
        if not idx.exists():
            return 0

        content = idx.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return 0
        parts = content.split("---", 2)
        if len(parts) < 3:
            return 0

        # B3 (2026-07-28, 台账 W28): 白名单摘要替代全量 frontmatter — post-compact 恰是
        # context 最紧张时刻。字段清单与 session-start.py INDEX_CORE 同步维护。
        import re as _re
        fm = {}
        for line in parts[1].splitlines():
            m = _re.match(r'\s*([\w\-_.]+)\s*:\s*"?([^"\n#]*)"?', line)
            if m:
                fm[m.group(1)] = m.group(2).strip()
        core = ["version", "path", "stage", "current_sprint_slug", "current_roadmap_slug",
                "next_action", "plan_model", "platforms_enabled"]
        lines = [f"{k}: {fm[k]}" for k in core if fm.get(k)]
        if not lines:
            return 0
        alerts = []
        if fm.get("design_changed_after_impl") == "true":
            alerts.append("🚨 design 改后未重新 review: ship 前必须重新 review, delivery-gate 会 block.")
        na = fm.get("next_action", "")
        if na.startswith("next_roadmap_item:"):
            alerts.append(f"🎯 roadmap 推进: 进入 item {na.split(':', 1)[1]}.")
        body = "\n".join(lines) + "\n\n其余字段按需读 .ai_state/_index.md (历史/统计/能力探测不自动注入)."
        if alerts:
            body += "\n\n## 🚨 重要提醒\n\n" + "\n\n".join(alerts)
        additional = (
            "## Athena 项目状态 (post-compact restore)\n\n"
            + body
            + "\n\n详见 .ai_state/_index.md"
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostCompact",
                "additionalContext": additional,
            }
        }, ensure_ascii=False))
        return 0
    except Exception as e:
        sys.stderr.write(f"[compact-restore] non-blocking: {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
