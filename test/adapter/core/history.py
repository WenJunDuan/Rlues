"""History logging and log rotation.

Extracted from api_server.py — handles JSONL history file I/O and rotation.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional

from .state import get_state


LOG_DIR = Path(os.getenv("ADAPTER_LOG_DIR", ".ai_state/logs"))
LOG_FILE = LOG_DIR / "adapter.log"
HISTORY_FILE = LOG_DIR / "task_history.jsonl"
FILE_LOCK = threading.RLock()


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed >= minimum else default


HISTORY_MAX_BYTES = _int_env("ADAPTER_HISTORY_MAX_BYTES", 10 * 1024 * 1024)
HISTORY_BACKUP_COUNT = _int_env("ADAPTER_HISTORY_BACKUP_COUNT", 5)


def _init_logger() -> logging.Logger:
    logger = logging.getLogger("adapter.api_server")
    if logger.handlers:
        return logger

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    except (OSError, FileExistsError, PermissionError):
        logger.addHandler(logging.NullHandler())

    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


LOGGER = _init_logger()


def _history_archive_path(index: int) -> Path:
    return LOG_DIR / f"{HISTORY_FILE.name}.{index}"


def _list_history_files_locked() -> List[Path]:
    files: List[Path] = []
    for idx in range(HISTORY_BACKUP_COUNT, 0, -1):
        path = _history_archive_path(idx)
        if path.exists():
            files.append(path)
    if HISTORY_FILE.exists():
        files.append(HISTORY_FILE)
    return files


def _rotate_history_logs_locked(force: bool = False) -> bool:
    if not HISTORY_FILE.exists():
        return False
    if not force and HISTORY_FILE.stat().st_size < HISTORY_MAX_BYTES:
        return False

    for idx in range(HISTORY_BACKUP_COUNT, 0, -1):
        src = HISTORY_FILE if idx == 1 else _history_archive_path(idx - 1)
        dst = _history_archive_path(idx)
        if not src.exists():
            continue
        if idx == HISTORY_BACKUP_COUNT and dst.exists():
            dst.unlink()
        src.replace(dst)
    return True


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def write_history_record(action: str, task_id: str, payload: Dict[str, Any]) -> None:
    """Write a history record to JSONL file and to the store backend."""
    record = {
        "timestamp": _utc_now(),
        "action": action,
        "task_id": task_id,
        "payload": payload,
    }
    line = json.dumps(record, ensure_ascii=False)

    # File-based history (backward compat)
    try:
        with FILE_LOCK:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            _rotate_history_logs_locked(force=False)
            with HISTORY_FILE.open("a", encoding="utf-8") as fp:
                fp.write(line + "\n")
    except (OSError, PermissionError):
        pass

    # Store-backed history
    try:
        state = get_state()
        state.store.save_history(record)
    except Exception:
        pass

    LOGGER.info("%s %s", action, line)


def list_logs(task_id: Optional[str] = None, *, limit: int = 200) -> Dict[str, Any]:
    """Read persisted adapter logs from history JSONL file."""
    from .error_codes import VALIDATION_INVALID_VALUE, error_payload

    if limit <= 0:
        return {
            "status": "failed",
            "error": error_payload(VALIDATION_INVALID_VALUE, "limit must be > 0", recoverable=True),
        }

    if task_id is not None and (not isinstance(task_id, str) or not task_id.strip()):
        return {
            "status": "failed",
            "error": error_payload(VALIDATION_INVALID_VALUE, "task_id must be non-empty string", recoverable=True),
        }
    task_id = task_id.strip() if isinstance(task_id, str) else None

    # Try store backend first
    try:
        state = get_state()
        rows = state.store.list_history(task_id=task_id, limit=limit)
        if rows:
            return {
                "status": "ok",
                "count": len(rows),
                "logs": rows,
                "storage": {"backend": "store", "log_file": str(LOG_FILE)},
            }
    except Exception:
        pass

    # Fallback to file-based logs
    with FILE_LOCK:
        files = _list_history_files_locked()

    if not files:
        return {
            "status": "ok",
            "count": 0,
            "logs": [],
            "storage": {"log_file": str(LOG_FILE), "history_file": str(HISTORY_FILE), "history_archives": []},
        }

    lines: List[str] = []
    for path in files:
        try:
            lines.extend(path.read_text(encoding="utf-8").splitlines())
        except Exception:
            continue

    rows_file: List[Dict[str, Any]] = []
    for file_line in lines:
        if not file_line.strip():
            continue
        try:
            row = json.loads(file_line)
        except json.JSONDecodeError:
            continue
        if task_id is not None and row.get("task_id") != task_id:
            continue
        if isinstance(row, dict):
            rows_file.append(row)

    rows_file = rows_file[-limit:]
    archives = [str(path) for path in files if path != HISTORY_FILE]
    return {
        "status": "ok",
        "count": len(rows_file),
        "logs": rows_file,
        "storage": {"log_file": str(LOG_FILE), "history_file": str(HISTORY_FILE), "history_archives": archives},
    }


def archive_logs(*, force: bool = False) -> Dict[str, Any]:
    """Rotate history logs and keep backups."""
    with FILE_LOCK:
        rotated = _rotate_history_logs_locked(force=force)
        files = _list_history_files_locked()
    return {
        "status": "ok",
        "rotated": rotated,
        "force": force,
        "files": [str(path) for path in files],
        "max_bytes": HISTORY_MAX_BYTES,
        "backup_count": HISTORY_BACKUP_COUNT,
    }
