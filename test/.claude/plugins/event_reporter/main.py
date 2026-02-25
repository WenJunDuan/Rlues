"""Event reporter with file-backed storage and unified response envelope."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4


PLUGIN = "event_reporter"
MAX_BUFFER = 2000
DEFAULT_EVENT_PATH = ".ai_state/runtime/events/events.jsonl"
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


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _event_file() -> Path:
    path = os.environ.get("EVENT_REPORTER_PATH", DEFAULT_EVENT_PATH)
    return Path(path).expanduser()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _read_events() -> List[dict]:
    path = _event_file()
    if not path.exists():
        return []

    events: List[dict] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                try:
                    item = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    events.append(item)
    except OSError:
        return []
    return events


def _write_events(events: List[dict]) -> None:
    path = _event_file()
    _ensure_parent(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    temp.replace(path)


def _append_event(event: dict) -> int:
    path = _event_file()
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    events = _read_events()
    if len(events) > MAX_BUFFER:
        events = events[-MAX_BUFFER:]
        _write_events(events)
    return len(events)


def report(task_id: str, event_type: str, payload: dict) -> dict:
    data: Dict[str, Any] = {"task_id": task_id, "event_type": event_type, "payload": payload}

    if not isinstance(task_id, str) or not task_id.strip():
        return _resp(False, "EVENT_INVALID_TASK_ID", "task_id must be non-empty string", data)
    if not isinstance(event_type, str) or not event_type.strip():
        return _resp(False, "EVENT_INVALID_TYPE", "event_type must be non-empty string", data)
    if not isinstance(payload, dict):
        return _resp(False, "EVENT_INVALID_PAYLOAD", "payload must be object", data)

    normalized_type = event_type.strip()
    event = {
        "event_id": f"evt_{uuid4().hex[:12]}",
        "task_id": task_id.strip(),
        "timestamp": _utc_now(),
        "type": normalized_type,
        "data": payload,
        "known_type": normalized_type in ALLOWED_TYPES,
    }

    try:
        buffer_size = _append_event(event)
    except OSError as exc:
        return _resp(False, "EVENT_STORE_ERROR", "failed to persist event", {**data, "error": str(exc)})

    code = "OK" if event["known_type"] else "EVENT_UNKNOWN_TYPE"
    message = "event stored" if event["known_type"] else "event stored with unknown type"
    return _resp(True, code, message, {"event": event, "buffer_size": buffer_size})


def list_events(task_id: str | None = None, limit: int = 100) -> dict:
    if task_id is not None and (not isinstance(task_id, str) or not task_id.strip()):
        return _resp(False, "EVENT_INVALID_TASK_ID", "task_id must be non-empty string", {"task_id": task_id, "limit": limit})
    if not isinstance(limit, int) or limit <= 0:
        return _resp(False, "EVENT_INVALID_LIMIT", "limit must be positive integer", {"task_id": task_id, "limit": limit})

    rows = _read_events()
    if isinstance(task_id, str) and task_id.strip():
        rows = [event for event in rows if event.get("task_id") == task_id.strip()]

    sliced = rows[-limit:]
    return _resp(True, "OK", "events listed", {"events": sliced, "count": len(sliced)})


def clear_events(task_id: str | None = None) -> dict:
    if task_id is not None and (not isinstance(task_id, str) or not task_id.strip()):
        return _resp(False, "EVENT_INVALID_TASK_ID", "task_id must be non-empty string", {"task_id": task_id})

    rows = _read_events()
    if task_id is None:
        removed = len(rows)
        _write_events([])
        return _resp(True, "OK", "all events cleared", {"removed": removed})

    key = task_id.strip()
    kept = [event for event in rows if event.get("task_id") != key]
    removed = len(rows) - len(kept)
    _write_events(kept)
    return _resp(True, "OK", "task events cleared", {"task_id": key, "removed": removed})


def _parse_json(value: str | None) -> Any:
    text = (value or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def _extract_task_id(values: List[Any]) -> str:
    for value in values:
        if isinstance(value, dict):
            for key in ("task_id", "taskId"):
                item = value.get(key)
                if isinstance(item, str) and item.strip():
                    return item.strip()
            for nested_key in ("input", "payload", "args", "arguments"):
                nested = value.get(nested_key)
                if nested is not None:
                    task_id = _extract_task_id([nested])
                    if task_id:
                        return task_id
        elif isinstance(value, list):
            task_id = _extract_task_id(value)
            if task_id:
                return task_id
    fallback = os.getenv("TASK_ID") or os.getenv("CLAUDE_TASK_ID")
    return fallback.strip() if isinstance(fallback, str) and fallback.strip() else "unknown_task"


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {"value": value}


def _arg_text(args: dict, key: str) -> str:
    value = args.get(key)
    return value if isinstance(value, str) else ""


def _cli() -> dict:
    action = sys.argv[1] if len(sys.argv) > 1 else "help"

    if action == "tool_call":
        tool_input = _parse_json(sys.argv[2] if len(sys.argv) > 2 else os.getenv("TOOL_INPUT", ""))
        tool_output = _parse_json(sys.argv[3] if len(sys.argv) > 3 else os.getenv("TOOL_OUTPUT", ""))
        task_id = _extract_task_id([tool_input, tool_output])
        payload = {
            "tool_input": tool_input,
            "tool_output": tool_output,
        }
        return report(task_id=task_id, event_type="tool_call", payload=payload)

    args = _parse_json(sys.argv[2] if len(sys.argv) > 2 else "{}")
    if not isinstance(args, dict):
        args = {}

    if action == "report":
        return report(
            task_id=_arg_text(args, "task_id"),
            event_type=_arg_text(args, "event_type"),
            payload=_as_dict(args.get("payload", {})),
        )
    if action == "list_events":
        limit = args.get("limit", 100)
        if not isinstance(limit, int):
            limit = 100
        return list_events(task_id=args.get("task_id"), limit=limit)
    if action == "clear_events":
        return clear_events(task_id=args.get("task_id"))

    return _resp(False, "EVENT_INVALID_ACTION", "supported actions: tool_call|report|list_events|clear_events", {"action": action})


if __name__ == "__main__":
    try:
        print(json.dumps(_cli(), ensure_ascii=False))
    except Exception as exc:  # pragma: no cover
        print(
            json.dumps(
                _resp(False, "EVENT_RUNTIME_ERROR", "event_reporter runtime error", {"error": str(exc)}),
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)
