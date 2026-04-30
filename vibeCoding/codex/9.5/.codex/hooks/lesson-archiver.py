#!/usr/bin/env python3
"""
VibeCoding lesson-archiver

把 ~/.codex/lessons/draft-*.md 中超过 7 天的移到 archive/
不是独立 hook, 由 session-start.py 在 startup 时调用一次。
也可手动: python3 ~/.codex/hooks/lesson-archiver.py
"""
import os
import sys
from pathlib import Path
import time


SEVEN_DAYS = 7 * 24 * 60 * 60


def main():
    home = Path.home()
    lessons_dir = home / ".codex" / "lessons"
    archive_dir = lessons_dir / "archive"

    if not lessons_dir.is_dir():
        sys.exit(0)

    archive_dir.mkdir(exist_ok=True)

    now = time.time()
    archived = 0

    for f in lessons_dir.iterdir():
        if not f.is_file():
            continue
        if not f.name.startswith("draft-"):
            continue
        if not f.name.endswith(".md"):
            continue

        age = now - f.stat().st_mtime
        if age > SEVEN_DAYS:
            try:
                f.rename(archive_dir / f.name)
                archived += 1
            except Exception as e:
                sys.stderr.write(f"[lesson-archiver] archive 失败 {f.name}: {e}\n")

    if archived > 0:
        sys.stderr.write(f"[lesson-archiver] 归档 {archived} 个超期 draft\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
