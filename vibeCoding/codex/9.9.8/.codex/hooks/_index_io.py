"""VibeCoding Athena v9.9.6 · _index.md 并发安全读写 (CX)

同一事件的 command hooks 并发执行、不保证顺序 (Codex 官方)。
index-updater / design-change-detector / pace-continuator 都对 _index.md
做 read-modify-write, 并发下后写覆盖先写 = lost update, 丢的是
design_changed_after_impl 这类门禁标记 —— 丢了不报错, 只静默放行。

方案: O_EXCL 锁文件 (含 stale 自动打破) + tmp/replace 原子替换。
拿不到锁退化为直接写并告警, 不阻塞 hook。
"""

from __future__ import annotations

import atexit
import os
import sys
import time
from pathlib import Path
from typing import Callable

LOCK_STALE_S = 10.0
MAX_WAIT_S = 0.8
SLEEP_S = 0.025


def _lock_path(idx: Path) -> Path:
    return idx.with_name(idx.name + ".lock")


def acquire(idx: Path) -> bool:
    lp = _lock_path(idx)
    deadline = time.monotonic() + MAX_WAIT_S
    while True:
        try:
            os.close(os.open(str(lp), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
            atexit.register(lambda: release(idx))
            return True
        except FileExistsError:
            try:
                if time.time() - lp.stat().st_mtime > LOCK_STALE_S:
                    lp.unlink(missing_ok=True)
                    continue
            except OSError:
                continue
            if time.monotonic() > deadline:
                sys.stderr.write("[_index_io] 锁等待超时, 退化为直接写 (可能丢更新)\n")
                return False
            time.sleep(SLEEP_S)
        except OSError:
            return False


def release(idx: Path) -> None:
    try:
        _lock_path(idx).unlink(missing_ok=True)
    except OSError:
        pass


def write_atomic(idx: Path, content: str) -> None:
    tmp = idx.with_name(f"{idx.name}.tmp.{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    os.replace(str(tmp), str(idx))


def update(idx: Path, mutate: Callable[[str], str | None]) -> str | None:
    """读-改-写全程持锁。mutate 返回 None 或相同内容则不写。"""
    locked = acquire(idx)
    try:
        content = idx.read_text(encoding="utf-8")
        nxt = mutate(content)
        if nxt is not None and nxt != content:
            write_atomic(idx, nxt)
        return nxt
    finally:
        if locked:
            release(idx)
