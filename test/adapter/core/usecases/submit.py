"""Task submission use case."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from ..error_codes import ADAPTER_PARSE_ERROR, VALIDATION_INVALID_VALUE, error_payload, hash_api_key
from ..history import write_history_record
from ..scheduler import schedule_workers, upsert_task_meta
from ..state import get_state
from ..task_queue import QueueItem
from ..types import from_dict
from ..validators import validate_task_envelope


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
        owner_hash = hash_api_key(owner_api_key)
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
