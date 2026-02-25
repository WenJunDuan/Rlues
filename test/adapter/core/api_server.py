"""Framework-agnostic API layer for minimal runnable chain.

This file provides callable functions that mirror endpoint behavior.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import DEFAULT_CONFIG
from .error_codes import (
    ADAPTER_EXECUTION_ERROR,
    ADAPTER_PARSE_ERROR,
    ADAPTER_STREAM_NOT_FOUND,
    ADAPTER_TASK_NOT_FOUND,
    VALIDATION_FAILED,
    VALIDATION_INVALID_VALUE,
    error_payload,
)
from .event_pipeline import EventPipeline
from ..sdk.bridge import execute_task
from .task_queue import QueueItem, TaskQueue
from .types import ResultEnvelope, TaskEnvelope, from_dict
from .validators import validate_result_envelope, validate_task_envelope


QUEUE = TaskQueue(max_concurrent=DEFAULT_CONFIG.max_concurrent_sessions)
EVENTS = EventPipeline(max_events_per_task=DEFAULT_CONFIG.max_events_per_task)
TASK_STORE: Dict[str, TaskEnvelope] = {}
RESULT_STORE: Dict[str, ResultEnvelope] = {}
TASK_META: Dict[str, Dict[str, Any]] = {}
RUNNING_TASKS: set[str] = set()
SESSION_FUTURES: Dict[str, Future[None]] = {}
STORE_LOCK = threading.RLock()

WORKER_POOL = ThreadPoolExecutor(
    max_workers=DEFAULT_CONFIG.max_concurrent_sessions,
    thread_name_prefix="adapter-session",
)

LOG_DIR = Path(os.getenv("ADAPTER_LOG_DIR", ".ai_state/logs"))
LOG_FILE = LOG_DIR / "adapter.log"
HISTORY_FILE = LOG_DIR / "task_history.jsonl"
FILE_LOCK = threading.RLock()
STATE_DIR = Path(os.getenv("ADAPTER_STATE_DIR", ".ai_state/state"))
STATE_FILE = STATE_DIR / "adapter_state.json"
STATE_VERSION = 1


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_api_key(token: Optional[str]) -> Optional[str]:
    if not isinstance(token, str):
        return None
    value = token.strip()
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _init_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("adapter.api_server")
    if logger.handlers:
        return logger

    handler = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
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


def _result_from_dict(data: Dict[str, Any]) -> Optional[ResultEnvelope]:
    if not isinstance(data, dict):
        return None
    try:
        return ResultEnvelope(
            task_id=str(data["task_id"]),
            command=str(data["command"]),
            status=str(data["status"]),
            result=data.get("result", {}) if isinstance(data.get("result"), dict) else {},
            execution=data.get("execution", {}) if isinstance(data.get("execution"), dict) else {},
            error=data.get("error") if (data.get("error") is None or isinstance(data.get("error"), dict)) else None,
        )
    except Exception:
        return None


def _snapshot_state_locked() -> Dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "timestamp": _utc_now(),
        "tasks": {task_id: asdict(task) for task_id, task in TASK_STORE.items()},
        "results": {task_id: asdict(result) for task_id, result in RESULT_STORE.items()},
        "task_meta": TASK_META,
        "queue_lanes": {
            session_key: [item.task_id for item in lane]
            for session_key, lane in QUEUE.lanes.items()
            if lane
        },
        "running_tasks": sorted(list(RUNNING_TASKS)),
    }


def _persist_state_locked() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = _snapshot_state_locked()
    tmp_path = STATE_FILE.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(STATE_FILE)


def _load_state_from_disk() -> Dict[str, int]:
    if not STATE_FILE.exists():
        return {"tasks": 0, "results": 0, "queued": 0}

    try:
        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        LOGGER.exception("failed to load persisted state file: %s", STATE_FILE)
        return {"tasks": 0, "results": 0, "queued": 0}

    if not isinstance(raw, dict):
        return {"tasks": 0, "results": 0, "queued": 0}

    restored_tasks = 0
    restored_results = 0

    tasks_blob = raw.get("tasks")
    if isinstance(tasks_blob, dict):
        for task_id, task_data in tasks_blob.items():
            if not isinstance(task_data, dict):
                continue
            try:
                task = from_dict(task_data)
            except Exception:
                continue
            TASK_STORE[str(task_id)] = task
            restored_tasks += 1

    results_blob = raw.get("results")
    if isinstance(results_blob, dict):
        for task_id, result_data in results_blob.items():
            if not isinstance(result_data, dict):
                continue
            result = _result_from_dict(result_data)
            if result is None:
                continue
            RESULT_STORE[str(task_id)] = result
            restored_results += 1

    meta_blob = raw.get("task_meta")
    if isinstance(meta_blob, dict):
        for task_id, meta in meta_blob.items():
            if not isinstance(meta, dict):
                continue
            TASK_META[str(task_id)] = dict(meta)

    # Rebuild queue lanes from persisted order.
    queue_blob = raw.get("queue_lanes")
    if isinstance(queue_blob, dict):
        for session_key, task_ids in queue_blob.items():
            if not isinstance(session_key, str) or not isinstance(task_ids, list):
                continue
            for task_id in task_ids:
                if not isinstance(task_id, str):
                    continue
                if task_id not in TASK_STORE or task_id in RESULT_STORE:
                    continue
                QUEUE.enqueue(QueueItem(task_id=task_id, session_key=session_key))
                meta = TASK_META.get(task_id)
                if isinstance(meta, dict):
                    meta["status"] = "queued"
                    meta["updated_at"] = _utc_now()

    running_blob = raw.get("running_tasks")
    if isinstance(running_blob, list):
        for task_id in running_blob:
            if not isinstance(task_id, str):
                continue
            if task_id not in TASK_STORE or task_id in RESULT_STORE:
                continue
            meta = TASK_META.get(task_id)
            if not isinstance(meta, dict):
                meta = {}
                TASK_META[task_id] = meta
            in_queue = any(task_id in [item.task_id for item in lane] for lane in QUEUE.lanes.values())
            if not in_queue:
                session_key = (
                    str(meta.get("session_key"))
                    if isinstance(meta, dict) and meta.get("session_key")
                    else QUEUE.build_session_key(TASK_STORE[task_id].context.tenant_id, TASK_STORE[task_id].context.operator_id)
                )
                QUEUE.enqueue(QueueItem(task_id=task_id, session_key=session_key))
            meta["status"] = "queued"
            meta["updated_at"] = _utc_now()

    queued_count = QUEUE.total_pending()
    LOGGER.info(
        "state restored: tasks=%s results=%s queued=%s file=%s",
        restored_tasks,
        restored_results,
        queued_count,
        STATE_FILE,
    )
    return {"tasks": restored_tasks, "results": restored_results, "queued": queued_count}


def _write_history_record(action: str, task_id: str, payload: Dict[str, Any]) -> None:
    record = {
        "timestamp": _utc_now(),
        "action": action,
        "task_id": task_id,
        "payload": payload,
    }
    line = json.dumps(record, ensure_ascii=False)

    with FILE_LOCK:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        _rotate_history_logs_locked(force=False)
        with HISTORY_FILE.open("a", encoding="utf-8") as fp:
            fp.write(line + "\n")

    LOGGER.info("%s %s", action, line)


def _emit_event(task_id: str, event_type: str, data: Dict[str, Any]) -> None:
    with STORE_LOCK:
        EVENTS.emit(task_id, event_type, data)


def _build_failed_result(
    task: TaskEnvelope,
    code: str,
    message: str,
    recoverable: bool,
    details: Optional[List[dict]] = None,
) -> ResultEnvelope:
    return ResultEnvelope(
        task_id=task.task_id,
        command=task.command,
        status="failed",
        result={
            "decision": "needs_review",
            "confidence": 0.0,
            "summary": message,
            "issues": [{"severity": "error", "category": code, "description": message}],
            "evidence": [],
        },
        execution={
            "model_used": task.runtime.model or "sonnet",
            "agents_invoked": [],
            "parallel_tasks": 0,
            "tools_called": [],
        },
        error=error_payload(code, message, details=details, recoverable=recoverable),
    )


def _upsert_task_meta(
    task: TaskEnvelope,
    session_key: str,
    status: str,
    *,
    owner_api_key_hash: Optional[str] = None,
) -> None:
    now = _utc_now()
    current = TASK_META.get(task.task_id)
    created_at = current.get("created_at") if isinstance(current, dict) and current.get("created_at") else now
    existing_owner_hash = (
        str(current.get("owner_api_key_hash")).strip()
        if isinstance(current, dict) and current.get("owner_api_key_hash")
        else None
    )
    owner_hash = owner_api_key_hash or existing_owner_hash
    TASK_META[task.task_id] = {
        "task_id": task.task_id,
        "command": task.command,
        "tenant_id": task.context.tenant_id,
        "operator_id": task.context.operator_id,
        "session_key": session_key,
        "status": status,
        "created_at": created_at,
        "updated_at": now,
        "started_at": current.get("started_at") if isinstance(current, dict) else None,
        "finished_at": current.get("finished_at") if isinstance(current, dict) else None,
        "owner_api_key_hash": owner_hash,
    }


def _mark_task_started(task_id: str) -> None:
    meta = TASK_META.get(task_id)
    if not isinstance(meta, dict):
        return
    now = _utc_now()
    meta["status"] = "processing"
    meta["updated_at"] = now
    if not meta.get("started_at"):
        meta["started_at"] = now


def _mark_task_finished(task_id: str, status: str, decision: str) -> None:
    meta = TASK_META.get(task_id)
    if not isinstance(meta, dict):
        return
    now = _utc_now()
    meta["status"] = status
    meta["decision"] = decision
    meta["updated_at"] = now
    meta["finished_at"] = now


def _next_ready_session() -> Optional[str]:
    for session_key in QUEUE.pending_session_keys():
        if QUEUE.can_start_session(session_key) and session_key not in SESSION_FUTURES:
            return session_key
    return None


def _on_session_done(session_key: str, fut: Future[None]) -> None:
    exc = fut.exception()
    if exc is not None:
        LOGGER.exception("session worker failed: session=%s, error=%s", session_key, exc)

    with STORE_LOCK:
        QUEUE.mark_session_done(session_key)
        SESSION_FUTURES.pop(session_key, None)

    _schedule_workers()


def _schedule_workers() -> None:
    with STORE_LOCK:
        while True:
            session_key = _next_ready_session()
            if session_key is None:
                break
            QUEUE.mark_session_start(session_key)
            future = WORKER_POOL.submit(_drain_session_worker, session_key)
            SESSION_FUTURES[session_key] = future
            future.add_done_callback(lambda f, s=session_key: _on_session_done(s, f))


def _bootstrap_runtime() -> None:
    with STORE_LOCK:
        summary = _load_state_from_disk()
    if summary.get("queued", 0) > 0:
        _schedule_workers()


def _drain_session_worker(session_key: str) -> None:
    while True:
        with STORE_LOCK:
            item = QUEUE.dequeue_next(session_key)
            if item is None:
                return
            task = TASK_STORE.get(item.task_id)
            if task is not None:
                RUNNING_TASKS.add(item.task_id)
                _mark_task_started(item.task_id)
                _persist_state_locked()

        if task is None:
            _emit_event(item.task_id, "error", {"code": ADAPTER_TASK_NOT_FOUND, "message": "task envelope not found in store"})
            _emit_event(item.task_id, "task_end", {"status": "failed", "reason": "task_not_found"})
            _write_history_record("task_missing", item.task_id, {"session_key": session_key})
            continue

        try:
            sdk_result = execute_task(task)
            result_dict = asdict(sdk_result.envelope)
            output_validation = validate_result_envelope(result_dict)
            if not output_validation["ok"]:
                message = f"result envelope validation failed: {output_validation['message']}"
                details = output_validation.get("details", [])
                for ev in sdk_result.events:
                    if ev.get("type") == "task_end":
                        continue
                    _emit_event(item.task_id, ev["type"], ev.get("data", {}))
                _emit_event(item.task_id, "error", {"code": VALIDATION_FAILED, "message": message, "details": details})
                _emit_event(item.task_id, "task_end", {"status": "failed", "reason": "result_validation_failed"})

                failed = _build_failed_result(
                    task=task,
                    code=VALIDATION_FAILED,
                    message=message,
                    recoverable=False,
                    details=details,
                )
                with STORE_LOCK:
                    RESULT_STORE[item.task_id] = failed
                    _mark_task_finished(item.task_id, failed.status, str(failed.result.get("decision", "needs_review")))
                    _persist_state_locked()
                _write_history_record(
                    "task_failed",
                    item.task_id,
                    {"status": failed.status, "reason": "result_validation_failed", "code": VALIDATION_FAILED},
                )
                continue

            with STORE_LOCK:
                RESULT_STORE[item.task_id] = sdk_result.envelope
                _mark_task_finished(
                    item.task_id,
                    sdk_result.envelope.status,
                    str(sdk_result.envelope.result.get("decision", "needs_review")),
                )
                _persist_state_locked()
            for ev in sdk_result.events:
                _emit_event(item.task_id, ev["type"], ev.get("data", {}))
            _write_history_record(
                "task_completed",
                item.task_id,
                {
                    "status": sdk_result.envelope.status,
                    "decision": sdk_result.envelope.result.get("decision"),
                    "confidence": sdk_result.envelope.result.get("confidence"),
                },
            )
        except Exception as exc:
            message = f"adapter execution error: {exc}"
            failed = _build_failed_result(
                task=task,
                code=ADAPTER_EXECUTION_ERROR,
                message=message,
                recoverable=False,
            )
            with STORE_LOCK:
                RESULT_STORE[item.task_id] = failed
                _mark_task_finished(item.task_id, failed.status, str(failed.result.get("decision", "needs_review")))
                _persist_state_locked()
            _emit_event(item.task_id, "error", {"code": ADAPTER_EXECUTION_ERROR, "message": message})
            _emit_event(item.task_id, "task_end", {"status": "failed", "reason": "adapter_execution_error"})
            _write_history_record(
                "task_failed",
                item.task_id,
                {"status": failed.status, "reason": "adapter_execution_error", "code": ADAPTER_EXECUTION_ERROR},
            )
        finally:
            with STORE_LOCK:
                RUNNING_TASKS.discard(item.task_id)
                _persist_state_locked()


_bootstrap_runtime()


def submit_task(payload: Dict[str, Any], *, owner_api_key: Optional[str] = None) -> Dict[str, Any]:
    """Equivalent to POST /task behavior."""
    validation = validate_task_envelope(payload)
    if not validation["ok"]:
        return {
            "status": "failed",
            "task_id": payload.get("task_id", ""),
            "error": error_payload(
                validation["code"],
                validation["message"],
                details=validation.get("details", []),
                recoverable=True,
            ),
        }

    try:
        task = from_dict(payload)
    except Exception as exc:
        return {
            "status": "failed",
            "task_id": payload.get("task_id", ""),
            "error": error_payload(ADAPTER_PARSE_ERROR, f"failed to parse envelope: {exc}", recoverable=False),
        }

    with STORE_LOCK:
        if task.task_id in TASK_STORE or task.task_id in RESULT_STORE:
            return {
                "status": "failed",
                "task_id": task.task_id,
                "error": error_payload(
                    VALIDATION_INVALID_VALUE,
                    "task_id already exists",
                    details=[{"path": "task_id", "reason": "duplicate"}],
                    recoverable=True,
                ),
            }

        session_key = QUEUE.build_session_key(task.context.tenant_id, task.context.operator_id)
        owner_hash = _hash_api_key(owner_api_key)
        TASK_STORE[task.task_id] = task
        _upsert_task_meta(
            task,
            session_key=session_key,
            status="queued",
            owner_api_key_hash=owner_hash,
        )
        lane_pos = QUEUE.enqueue(QueueItem(task_id=task.task_id, session_key=session_key))
        EVENTS.emit(task.task_id, "task_queued", {"session_key": session_key, "lane_pos": lane_pos})
        _persist_state_locked()

    _write_history_record(
        "task_queued",
        task.task_id,
        {"session_key": session_key, "command": task.command, "lane_pos": lane_pos},
    )
    _schedule_workers()

    with STORE_LOCK:
        status = "processing" if task.task_id in RUNNING_TASKS else "queued"

    return {
        "status": status,
        "task_id": task.task_id,
        "session_key": session_key,
        "lane_pos": lane_pos,
    }


def get_task_meta(task_id: str) -> Optional[Dict[str, Any]]:
    with STORE_LOCK:
        meta = TASK_META.get(task_id)
        if not isinstance(meta, dict):
            return None
        return dict(meta)


def get_result(task_id: str) -> Dict[str, Any]:
    """Equivalent to GET /task/{task_id}."""
    with STORE_LOCK:
        result = RESULT_STORE.get(task_id)
        if result is None:
            meta = TASK_META.get(task_id)
            if isinstance(meta, dict):
                return {
                    "status": str(meta.get("status", "queued")),
                    "task_id": task_id,
                    "command": meta.get("command"),
                    "meta": meta,
                }
            return {
                "status": "not_found",
                "task_id": task_id,
                "error": error_payload(ADAPTER_TASK_NOT_FOUND, "task result not found", recoverable=True),
            }
        return asdict(result)


def get_compliance_feedback(task_id: str) -> Dict[str, Any]:
    """External-facing concise feedback: compliance + one basis."""
    with STORE_LOCK:
        result = RESULT_STORE.get(task_id)
        if result is None:
            meta = TASK_META.get(task_id)
            if isinstance(meta, dict):
                status = str(meta.get("status", "queued"))
                return {
                    "status": status,
                    "task_id": task_id,
                    "compliance": "needs_review",
                    "basis": "task is still running; please poll later",
                }
            return {
                "status": "not_found",
                "task_id": task_id,
                "error": error_payload(ADAPTER_TASK_NOT_FOUND, "task result not found", recoverable=True),
            }
        result_dict = asdict(result)

    decision = str(result_dict.get("result", {}).get("decision", "")).strip().lower()
    compliance = "needs_review"
    if decision == "approved":
        compliance = "compliant"
    elif decision == "rejected":
        compliance = "non_compliant"

    basis = str(result_dict.get("result", {}).get("summary", "")).strip()
    if not basis:
        issues = result_dict.get("result", {}).get("issues", [])
        if isinstance(issues, list) and issues:
            first = issues[0]
            if isinstance(first, dict):
                basis = str(first.get("description", "")).strip()
    if not basis:
        basis = "manual review required due to insufficient evidence"

    return {"task_id": task_id, "compliance": compliance, "basis": basis[:180]}


def stream_events(task_id: str) -> Dict[str, Any]:
    """Equivalent to GET /task/{task_id}/events."""
    with STORE_LOCK:
        events = EVENTS.list_events(task_id)
        if not events and task_id not in TASK_STORE:
            return {
                "status": "not_found",
                "task_id": task_id,
                "error": error_payload(ADAPTER_STREAM_NOT_FOUND, "task events not found", recoverable=True),
            }
        return {"task_id": task_id, "events": events}


def list_history(
    *,
    limit: int = 50,
    offset: int = 0,
    command: Optional[str] = None,
    tenant_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List task history records from in-memory state."""
    if limit <= 0 or offset < 0:
        return {
            "status": "failed",
            "error": error_payload(
                VALIDATION_INVALID_VALUE,
                "limit must be > 0 and offset must be >= 0",
                recoverable=True,
            ),
        }

    with STORE_LOCK:
        rows: List[Dict[str, Any]] = []
        for task_id, meta in TASK_META.items():
            row = dict(meta)
            envelope = RESULT_STORE.get(task_id)
            if envelope is not None:
                row["status"] = envelope.status
                row["decision"] = envelope.result.get("decision")
                row["summary"] = str(envelope.result.get("summary", ""))[:180]
            rows.append(row)

    def _ok(val: Optional[str], target: Optional[str]) -> bool:
        if target is None:
            return True
        return str(val or "").strip() == target.strip()

    rows = [
        r
        for r in rows
        if _ok(r.get("command"), command)
        and _ok(r.get("tenant_id"), tenant_id)
        and _ok(r.get("operator_id"), operator_id)
        and _ok(r.get("status"), status)
    ]
    rows.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    total = len(rows)
    items = rows[offset : offset + limit]
    return {
        "status": "ok",
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


def delete_history(task_id: str, *, purge_events: bool = True) -> Dict[str, Any]:
    """Delete a task's in-memory history and optionally its event stream."""
    if not isinstance(task_id, str) or not task_id.strip():
        return {
            "status": "failed",
            "task_id": task_id,
            "error": error_payload(VALIDATION_INVALID_VALUE, "task_id must be non-empty string", recoverable=True),
        }

    task_id = task_id.strip()
    with STORE_LOCK:
        if task_id in RUNNING_TASKS:
            return {
                "status": "failed",
                "task_id": task_id,
                "error": error_payload(
                    VALIDATION_INVALID_VALUE,
                    "task is running and cannot be deleted",
                    details=[{"path": "task_id", "reason": "running"}],
                    recoverable=True,
                ),
            }

        removed_from_queue = QUEUE.remove_task(task_id)
        had_task = TASK_STORE.pop(task_id, None) is not None
        had_result = RESULT_STORE.pop(task_id, None) is not None
        had_meta = TASK_META.pop(task_id, None) is not None
        removed_events = EVENTS.remove_task(task_id) if purge_events else 0
        changed = any([removed_from_queue, had_task, had_result, had_meta, bool(removed_events)])
        if changed:
            _persist_state_locked()

    if not changed:
        return {
            "status": "not_found",
            "task_id": task_id,
            "error": error_payload(ADAPTER_TASK_NOT_FOUND, "task history not found", recoverable=True),
        }

    _write_history_record(
        "task_deleted",
        task_id,
        {
            "removed_from_queue": removed_from_queue,
            "removed_task": had_task,
            "removed_result": had_result,
            "removed_meta": had_meta,
            "removed_events": removed_events,
        },
    )
    return {
        "status": "deleted",
        "task_id": task_id,
        "deleted": {
            "removed_from_queue": removed_from_queue,
            "removed_task": had_task,
            "removed_result": had_result,
            "removed_meta": had_meta,
            "removed_events": removed_events,
        },
    }


def list_logs(task_id: Optional[str] = None, *, limit: int = 200) -> Dict[str, Any]:
    """Read persisted adapter logs from history jsonl file."""
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

    rows: List[Dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if task_id is not None and row.get("task_id") != task_id:
            continue
        if isinstance(row, dict):
            rows.append(row)

    rows = rows[-limit:]
    archives = [str(path) for path in files if path != HISTORY_FILE]
    return {
        "status": "ok",
        "count": len(rows),
        "logs": rows,
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


def queue_runtime() -> Dict[str, Any]:
    """Expose queue and worker runtime status for diagnostics."""
    with STORE_LOCK:
        return {
            "status": "ok",
            "max_concurrent_sessions": QUEUE.max_concurrent,
            "running_sessions": sorted(list(QUEUE.running_sessions)),
            "running_tasks": sorted(list(RUNNING_TASKS)),
            "pending_sessions": QUEUE.pending_session_keys(),
            "pending_count": QUEUE.total_pending(),
            "worker_count": len(SESSION_FUTURES),
        }
