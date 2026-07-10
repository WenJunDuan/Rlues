#!/usr/bin/env python3
"""
VibeCoding Athena v9.9.1 · Codex PostCompact hook

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

        additional = (
            "## Athena 项目状态 (post-compact restore)\n\n"
            + parts[1].strip()
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
