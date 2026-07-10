#!/usr/bin/env python3
"""
VibeCoding Athena v9.9.1 · Codex PreCompact hook

职责: compact 前快照 .ai_state/_index.md 到 .ai_state/.snapshots/pre-compact-<ts>.md
前提: Codex 0.129+ 提供 PreCompact/PostCompact 事件 [官方 developers.openai.com/codex/hooks]
逻辑对齐 CC 端 compact-snapshot.cjs. 非阻塞.
"""
import sys
from datetime import datetime
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

        snap_dir = ai_state / ".snapshots"
        snap_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().isoformat().replace(":", "-").replace(".", "-")[:19]
        (snap_dir / f"pre-compact-{ts}.md").write_text(
            idx.read_text(encoding="utf-8"), encoding="utf-8"
        )
        return 0
    except Exception as e:
        sys.stderr.write(f"[compact-snapshot] non-blocking: {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
