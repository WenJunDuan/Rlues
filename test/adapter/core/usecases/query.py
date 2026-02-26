"""Task query and stream read use cases."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..error_codes import ADAPTER_STREAM_NOT_FOUND, ADAPTER_TASK_NOT_FOUND, error_payload
from ..state import get_state


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
