"""Event reporter MVP with unified response envelope."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4


PLUGIN = "event_reporter"
MAX_BUFFER = 2000
ALLOWED_TYPES = {
    "task_start",
    "task_queued",
    "context_loaded",
    "agent_dispatch",
    "task_spawn",
    "tool_call",
    "decision_point",
    "context_saved",
    "task_end",
    "error",
}
_EVENTS: List[dict] = []


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def _utc_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def report(task_id: str, event_type: str, payload: dict) -> dict:
    data: Dict[str, Any] = {"task_id": task_id, "event_type": event_type, "payload": payload}

    if not isinstance(task_id, str) or not task_id.strip():
        return _resp(False, "EVENT_INVALID_TASK_ID", "task_id must be non-empty string", data)
    if not isinstance(event_type, str) or not event_type.strip():
        return _resp(False, "EVENT_INVALID_TYPE", "event_type must be non-empty string", data)
    if not isinstance(payload, dict):
        return _resp(False, "EVENT_INVALID_PAYLOAD", "payload must be object", data)

    event = {
        "event_id": f"evt_{uuid4().hex[:12]}",
        "task_id": task_id.strip(),
        "timestamp": _utc_now(),
        "type": event_type.strip(),
        "data": payload,
        "known_type": event_type.strip() in ALLOWED_TYPES,
    }

    _EVENTS.append(event)
    if len(_EVENTS) > MAX_BUFFER:
        del _EVENTS[: len(_EVENTS) - MAX_BUFFER]

    code = "OK" if event["known_type"] else "EVENT_UNKNOWN_TYPE"
    message = "event stored" if event["known_type"] else "event stored with unknown type"
    return _resp(True, code, message, {"event": event, "buffer_size": len(_EVENTS)})


def list_events(task_id: str | None = None, limit: int = 100) -> dict:
    if task_id is not None and (not isinstance(task_id, str) or not task_id.strip()):
        return _resp(False, "EVENT_INVALID_TASK_ID", "task_id must be non-empty string", {"task_id": task_id, "limit": limit})
    if not isinstance(limit, int) or limit <= 0:
        return _resp(False, "EVENT_INVALID_LIMIT", "limit must be positive integer", {"task_id": task_id, "limit": limit})

    rows = _EVENTS
    if isinstance(task_id, str) and task_id.strip():
        rows = [e for e in _EVENTS if e.get("task_id") == task_id.strip()]
    return _resp(True, "OK", "events listed", {"events": rows[-limit:], "count": min(limit, len(rows))})


def clear_events(task_id: str | None = None) -> dict:
    if task_id is not None and (not isinstance(task_id, str) or not task_id.strip()):
        return _resp(False, "EVENT_INVALID_TASK_ID", "task_id must be non-empty string", {"task_id": task_id})

    if task_id is None:
        before = len(_EVENTS)
        _EVENTS.clear()
        return _resp(True, "OK", "all events cleared", {"removed": before})

    key = task_id.strip()
    before = len(_EVENTS)
    kept = [e for e in _EVENTS if e.get("task_id") != key]
    removed = before - len(kept)
    _EVENTS.clear()
    _EVENTS.extend(kept)
    return _resp(True, "OK", "task events cleared", {"task_id": key, "removed": removed})
