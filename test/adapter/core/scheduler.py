"""Worker pool and session scheduling.

Extracted from api_server.py — manages ThreadPoolExecutor, session drain
loop, and bootstrap logic.
"""

from __future__ import annotations

import hashlib
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from .config import DEFAULT_CONFIG
from .error_codes import (
    ADAPTER_EXECUTION_ERROR,
    ADAPTER_TASK_NOT_FOUND,
    VALIDATION_FAILED,
    error_payload,
)
from .history import LOGGER, write_history_record
from .state import get_state
from .task_queue import QueueItem
from .types import ResultEnvelope, TaskEnvelope, from_dict
from .validators import validate_result_envelope
from ..sdk.bridge import execute_task


SESSION_FUTURES: Dict[str, Future[None]] = {}

WORKER_POOL = ThreadPoolExecutor(
    max_workers=DEFAULT_CONFIG.max_concurrent_sessions,
    thread_name_prefix="adapter-session",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_api_key(token: Optional[str]) -> Optional[str]:
    if not isinstance(token, str):
        return None
    value = token.strip()
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _emit_event(task_id: str, event_type: str, data: Dict[str, Any]) -> None:
    state = get_state()
    with state.lock:
        state.events.emit(task_id, event_type, data)
        # Also persist to store backend
        event = {
            "task_id": task_id,
            "timestamp": _utc_now(),
            "type": event_type,
            "data": data,
        }
        try:
            state.store.save_event(task_id, event)
        except Exception:
            pass


def _build_failed_result(
    task: TaskEnvelope,
    code: str,
    message: str,
    recoverable: bool,
    details: Optional[list] = None,
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


def upsert_task_meta(
    task: TaskEnvelope,
    session_key: str,
    status: str,
    *,
    owner_api_key_hash: Optional[str] = None,
) -> None:
    state = get_state()
    now = _utc_now()
    current = state.store.get_meta(task.task_id)
    created_at = current.get("created_at") if isinstance(current, dict) and current.get("created_at") else now
    existing_owner_hash = (
        str(current.get("owner_api_key_hash")).strip()
        if isinstance(current, dict) and current.get("owner_api_key_hash")
        else None
    )
    owner_hash = owner_api_key_hash or existing_owner_hash
    meta = {
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
    state.store.save_meta(task.task_id, meta)


def _mark_task_started(task_id: str) -> None:
    state = get_state()
    meta = state.store.get_meta(task_id)
    if not isinstance(meta, dict):
        return
    now = _utc_now()
    meta["status"] = "processing"
    meta["updated_at"] = now
    if not meta.get("started_at"):
        meta["started_at"] = now
    state.store.save_meta(task_id, meta)


def _mark_task_finished(task_id: str, status: str, decision: str) -> None:
    state = get_state()
    meta = state.store.get_meta(task_id)
    if not isinstance(meta, dict):
        return
    now = _utc_now()
    meta["status"] = status
    meta["decision"] = decision
    meta["updated_at"] = now
    meta["finished_at"] = now
    state.store.save_meta(task_id, meta)


def _next_ready_session() -> Optional[str]:
    state = get_state()
    for session_key in state.queue.pending_session_keys():
        if state.queue.can_start_session(session_key) and session_key not in SESSION_FUTURES:
            return session_key
    return None


def _on_session_done(session_key: str, fut: Future[None]) -> None:
    exc = fut.exception()
    if exc is not None:
        LOGGER.exception("session worker failed: session=%s, error=%s", session_key, exc)

    state = get_state()
    with state.lock:
        state.queue.mark_session_done(session_key)
        SESSION_FUTURES.pop(session_key, None)

    schedule_workers()


def schedule_workers() -> None:
    """Find and start workers for ready sessions."""
    state = get_state()
    with state.lock:
        while True:
            session_key = _next_ready_session()
            if session_key is None:
                break
            state.queue.mark_session_start(session_key)
            future = WORKER_POOL.submit(_drain_session_worker, session_key)
            SESSION_FUTURES[session_key] = future
            future.add_done_callback(lambda f, s=session_key: _on_session_done(s, f))


def _drain_session_worker(session_key: str) -> None:
    """Drain all queued tasks for a session, executing them serially."""
    state = get_state()
    while True:
        task: Optional[TaskEnvelope] = None
        with state.lock:
            item = state.queue.dequeue_next(session_key)
            if item is None:
                return
            task_dict = state.store.get_task(item.task_id)
            if task_dict is not None:
                try:
                    task = from_dict(task_dict)
                except Exception:
                    task = None
            if task is not None:
                state.running_tasks.add(item.task_id)
                _mark_task_started(item.task_id)

        if task is None:
            _emit_event(item.task_id, "error", {"code": ADAPTER_TASK_NOT_FOUND, "message": "task envelope not found in store"})
            _emit_event(item.task_id, "task_end", {"status": "failed", "reason": "task_not_found"})
            write_history_record("task_missing", item.task_id, {"session_key": session_key})
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
                    task=task, code=VALIDATION_FAILED, message=message,
                    recoverable=False, details=details,
                )
                with state.lock:
                    state.store.save_result(item.task_id, asdict(failed))
                    _mark_task_finished(item.task_id, failed.status, str(failed.result.get("decision", "needs_review")))
                write_history_record(
                    "task_failed", item.task_id,
                    {"status": failed.status, "reason": "result_validation_failed", "code": VALIDATION_FAILED},
                )
                continue

            with state.lock:
                state.store.save_result(item.task_id, result_dict)
                _mark_task_finished(
                    item.task_id,
                    sdk_result.envelope.status,
                    str(sdk_result.envelope.result.get("decision", "needs_review")),
                )
            for ev in sdk_result.events:
                _emit_event(item.task_id, ev["type"], ev.get("data", {}))
            write_history_record(
                "task_completed", item.task_id,
                {
                    "status": sdk_result.envelope.status,
                    "decision": sdk_result.envelope.result.get("decision"),
                    "confidence": sdk_result.envelope.result.get("confidence"),
                },
            )
        except Exception as exc:
            message = f"adapter execution error: {exc}"
            failed = _build_failed_result(
                task=task, code=ADAPTER_EXECUTION_ERROR, message=message, recoverable=False,
            )
            with state.lock:
                state.store.save_result(item.task_id, asdict(failed))
                _mark_task_finished(item.task_id, failed.status, str(failed.result.get("decision", "needs_review")))
            _emit_event(item.task_id, "error", {"code": ADAPTER_EXECUTION_ERROR, "message": message})
            _emit_event(item.task_id, "task_end", {"status": "failed", "reason": "adapter_execution_error"})
            write_history_record(
                "task_failed", item.task_id,
                {"status": failed.status, "reason": "adapter_execution_error", "code": ADAPTER_EXECUTION_ERROR},
            )
        finally:
            with state.lock:
                state.running_tasks.discard(item.task_id)


def bootstrap_runtime() -> None:
    """Load persisted state and schedule pending workers on startup."""
    # For memory backend, nothing to restore from disk.
    # For postgres/redis, tasks in 'queued'/'processing' state will be
    # re-enqueued on next submit. The store already has the data.
    state = get_state()
    pending = state.queue.total_pending()
    if pending > 0:
        schedule_workers()
