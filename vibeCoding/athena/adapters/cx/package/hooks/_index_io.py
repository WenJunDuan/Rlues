"""Athena 9.9.9: owned lock, durable replace, no unlocked fallback."""
from __future__ import annotations
import atexit
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Callable

MAX_WAIT_S = 0.8
SLEEP_S = 0.025
LOCK_STALE_S = 10
_owned: dict[str, str] = {}

def _lock_path(idx: Path) -> Path:
    return idx.with_name(idx.name + '.lock')

def _legacy_lock_blocks(idx: Path) -> bool:
    lp = _lock_path(idx)
    try:
        st = lp.stat()
    except FileNotFoundError:
        return False
    pid = None
    try:
        data = json.loads(lp.read_text())
        if isinstance(data, dict) and isinstance(data.get('pid'), int):
            pid = data['pid']
    except (ValueError, OSError):
        pid = None
    if pid is not None:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            lp.unlink(missing_ok=True)
            return False
        except PermissionError:
            return True
    if time.time() - st.st_mtime > LOCK_STALE_S:
        lp.unlink(missing_ok=True)
        return False
    return True

def _contenders(idx: Path):
    prefix = idx.name + '.lock.'
    for file in idx.parent.iterdir():
        if not file.name.startswith(prefix) or not file.name.endswith('.json'):
            continue
        tail = file.name[len(prefix):-5].split('.')
        if len(tail) != 2 or not tail[0].isdigit():
            continue
        try:
            os.kill(int(tail[0]), 0)
        except ProcessLookupError:
            file.unlink(missing_ok=True)  # Unique per attempt; this pathname is never reused.
            continue
        except PermissionError:
            pass
        try:
            value = json.loads(file.read_text())
            yield file, value.get('ticket'), tail[1]
        except FileNotFoundError:
            continue
        except (ValueError, OSError):
            yield file, None, tail[1]  # Choosing: wait until its atomic ticket publication.


def acquire(idx: Path) -> bool:
    idx = Path(idx)
    key = str(idx.resolve())
    if key in _owned:
        return True
    token = uuid.uuid4().hex
    contender = idx.with_name(f'{idx.name}.lock.{os.getpid()}.{token}.json')
    deadline = time.monotonic() + MAX_WAIT_S
    try:
        # Lamport bakery tickets avoid racing stale-owner unlink/re-acquire.
        # The legacy .lock is honored, but never removed by a new contender.
        contender.write_text('{}')
        tickets = [n for _, n, _ in _contenders(idx) if isinstance(n, int)]
        ticket = max(tickets, default=0) + 1
        write_atomic(contender, json.dumps({'pid':os.getpid(),'ticket':ticket}))
        while True:
            blocked = _legacy_lock_blocks(idx)
            for file, number, other_token in _contenders(idx):
                if file == contender:
                    continue
                if number is None or (number,other_token) < (ticket,token):
                    blocked = True
            if not blocked:
                _owned[key] = str(contender)
                atexit.register(release,idx)
                return True
            if time.monotonic() >= deadline:
                sys.stderr.write('[_index_io] lock timeout; update skipped, original preserved\n')
                contender.unlink(missing_ok=True)
                return False
            time.sleep(SLEEP_S)
    except OSError as exc:
        contender.unlink(missing_ok=True)
        sys.stderr.write(f'[_index_io] lock unavailable; update skipped: {exc}\n')
        return False


def release(idx: Path) -> None:
    contender = _owned.pop(str(Path(idx).resolve()), None)
    if contender is not None:
        Path(contender).unlink(missing_ok=True)


def write_atomic(idx: Path, content: str) -> None:
    idx = Path(idx)
    if idx.exists() and idx.read_text(encoding='utf-8') == content:
        return
    tmp = idx.with_name(f'{idx.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}')
    try:
        with tmp.open('x', encoding='utf-8') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, idx)
        directory = os.open(idx.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        tmp.unlink(missing_ok=True)

def update(idx: Path, mutate: Callable[[str], str | None]) -> str | None:
    if not acquire(idx):
        return None
    try:
        content = Path(idx).read_text(encoding='utf-8')
        nxt = mutate(content)
        if nxt is not None and nxt != content:
            write_atomic(idx, nxt)
        return nxt
    finally:
        release(idx)
