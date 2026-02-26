"""History listing and deletion use cases."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..error_codes import ADAPTER_TASK_NOT_FOUND, VALIDATION_INVALID_VALUE, error_payload
from ..history import write_history_record
from ..state import get_state


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
