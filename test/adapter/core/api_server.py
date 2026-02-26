"""Framework-agnostic API layer — thin facade.

Delegates to state, scheduler, and history modules.
Public API surface remains unchanged.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from .config import DEFAULT_CONFIG
from .error_codes import (
    ADAPTER_PARSE_ERROR,
    ADAPTER_STREAM_NOT_FOUND,
    ADAPTER_TASK_NOT_FOUND,
    VALIDATION_INVALID_VALUE,
    error_payload,
)
from .history import LOGGER, archive_logs, list_logs, write_history_record
from .scheduler import (
    _hash_api_key,
    _emit_event,
    bootstrap_runtime,
    schedule_workers,
    upsert_task_meta,
)
from .state import get_state
from .task_queue import QueueItem
from .types import ResultEnvelope, TaskEnvelope, from_dict
from .validators import validate_task_envelope


# ── Bootstrap on import (backward compat) ──
bootstrap_runtime()


# ── Public API functions ──


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

    state = get_state()
    with state.lock:
        if state.store.has_task(task.task_id) or state.store.has_result(task.task_id):
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

        session_key = state.queue.build_session_key(task.context.tenant_id, task.context.operator_id)
        owner_hash = _hash_api_key(owner_api_key)
        state.store.save_task(task.task_id, asdict(task))
        upsert_task_meta(
            task,
            session_key=session_key,
            status="queued",
            owner_api_key_hash=owner_hash,
        )
        lane_pos = state.queue.enqueue(QueueItem(task_id=task.task_id, session_key=session_key))
        state.events.emit(task.task_id, "task_queued", {"session_key": session_key, "lane_pos": lane_pos})

    write_history_record(
        "task_queued",
        task.task_id,
        {"session_key": session_key, "command": task.command, "lane_pos": lane_pos},
    )
    schedule_workers()

    with state.lock:
        status = "processing" if task.task_id in state.running_tasks else "queued"

    return {
        "status": status,
        "task_id": task.task_id,
        "session_key": session_key,
        "lane_pos": lane_pos,
    }


def get_task_meta(task_id: str) -> Optional[Dict[str, Any]]:
    state = get_state()
    with state.lock:
        return state.store.get_meta(task_id)


def get_result(task_id: str) -> Dict[str, Any]:
    """Equivalent to GET /task/{task_id}."""
    state = get_state()
    with state.lock:
        result = state.store.get_result(task_id)
        if result is None:
            meta = state.store.get_meta(task_id)
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
        return result


def get_compliance_feedback(task_id: str) -> Dict[str, Any]:
    """External-facing concise feedback: compliance + one basis."""
    state = get_state()
    with state.lock:
        result = state.store.get_result(task_id)
        if result is None:
            meta = state.store.get_meta(task_id)
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

    decision = str(result.get("result", {}).get("decision", "")).strip().lower()
    compliance = "needs_review"
    if decision == "approved":
        compliance = "compliant"
    elif decision == "rejected":
        compliance = "non_compliant"

    basis = str(result.get("result", {}).get("summary", "")).strip()
    if not basis:
        issues = result.get("result", {}).get("issues", [])
        if isinstance(issues, list) and issues:
            first = issues[0]
            if isinstance(first, dict):
                basis = str(first.get("description", "")).strip()
    if not basis:
        basis = "manual review required due to insufficient evidence"

    return {"task_id": task_id, "compliance": compliance, "basis": basis[:180]}


def stream_events(task_id: str) -> Dict[str, Any]:
    """Equivalent to GET /task/{task_id}/events."""
    state = get_state()
    with state.lock:
        events = state.events.list_events(task_id)
        if not events and not state.store.has_task(task_id):
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
    """List task history records."""
    if limit <= 0 or offset < 0:
        return {
            "status": "failed",
            "error": error_payload(
                VALIDATION_INVALID_VALUE,
                "limit must be > 0 and offset must be >= 0",
                recoverable=True,
            ),
        }

    state = get_state()
    with state.lock:
        result = state.store.list_meta(
            command=command,
            tenant_id=tenant_id,
            operator_id=operator_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    return {
        "status": "ok",
        "total": result.get("total", 0),
        "limit": result.get("limit", limit),
        "offset": result.get("offset", offset),
        "items": result.get("items", []),
    }


def delete_history(task_id: str, *, purge_events: bool = True) -> Dict[str, Any]:
    """Delete a task's history and optionally its event stream."""
    if not isinstance(task_id, str) or not task_id.strip():
        return {
            "status": "failed",
            "task_id": task_id,
            "error": error_payload(VALIDATION_INVALID_VALUE, "task_id must be non-empty string", recoverable=True),
        }

    task_id = task_id.strip()
    state = get_state()
    with state.lock:
        if task_id in state.running_tasks:
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

        removed_from_queue = state.queue.remove_task(task_id)
        deleted = state.store.delete_task(task_id)
        removed_events = 0
        if purge_events:
            removed_events = state.events.remove_task(task_id)
        changed = any([
            removed_from_queue,
            deleted.get("removed_task"),
            deleted.get("removed_result"),
            deleted.get("removed_meta"),
            bool(removed_events),
        ])

    if not changed:
        return {
            "status": "not_found",
            "task_id": task_id,
            "error": error_payload(ADAPTER_TASK_NOT_FOUND, "task history not found", recoverable=True),
        }

    write_history_record(
        "task_deleted",
        task_id,
        {
            "removed_from_queue": removed_from_queue,
            "removed_task": deleted.get("removed_task", False),
            "removed_result": deleted.get("removed_result", False),
            "removed_meta": deleted.get("removed_meta", False),
            "removed_events": removed_events,
        },
    )
    return {
        "status": "deleted",
        "task_id": task_id,
        "deleted": {
            "removed_from_queue": removed_from_queue,
            "removed_task": deleted.get("removed_task", False),
            "removed_result": deleted.get("removed_result", False),
            "removed_meta": deleted.get("removed_meta", False),
            "removed_events": removed_events,
        },
    }


def queue_runtime() -> Dict[str, Any]:
    """Expose queue and worker runtime status for diagnostics."""
    state = get_state()
    with state.lock:
        return {
            "status": "ok",
            "max_concurrent_sessions": state.queue.max_concurrent,
            "running_sessions": sorted(list(state.queue.running_sessions)),
            "running_tasks": sorted(list(state.running_tasks)),
            "pending_sessions": state.queue.pending_session_keys(),
            "pending_count": state.queue.total_pending(),
            "worker_count": len(state.running_tasks),
        }
