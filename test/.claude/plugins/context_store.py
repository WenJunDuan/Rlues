"""Context store plugin MVP with unified response envelope."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


PLUGIN = "context_store"
_SESSION_STORE: Dict[str, Dict[str, dict]] = {}
_MEMORY_STORE: List[dict] = []


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def _tenant_operator_key(tenant_id: str, operator_id: str) -> str:
    return f"{tenant_id}:{operator_id}"


def _utc_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def load_session(tenant_id: str, operator_id: str, session_id: str | None = None) -> dict:
    data = {"tenant_id": tenant_id, "operator_id": operator_id, "session_id": session_id}

    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return _resp(False, "CONTEXT_INVALID_TENANT", "tenant_id must be non-empty string", data)
    if not isinstance(operator_id, str) or not operator_id.strip():
        return _resp(False, "CONTEXT_INVALID_OPERATOR", "operator_id must be non-empty string", data)

    key = _tenant_operator_key(tenant_id.strip(), operator_id.strip())
    sessions = _SESSION_STORE.get(key, {})
    if not sessions:
        return _resp(True, "CONTEXT_NOT_FOUND", "session not found", {**data, "session": None})

    if session_id:
        session = sessions.get(session_id)
        if session is None:
            return _resp(True, "CONTEXT_NOT_FOUND", "session_id not found", {**data, "session": None})
        return _resp(True, "OK", "session loaded", {**data, "session": session})

    latest = max(sessions.values(), key=lambda x: x.get("updated_at", ""))
    return _resp(True, "OK", "latest session loaded", {**data, "session": latest})


def save_session(tenant_id: str, operator_id: str, task_id: str, payload: dict) -> dict:
    data = {"tenant_id": tenant_id, "operator_id": operator_id, "task_id": task_id, "payload": payload}

    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return _resp(False, "CONTEXT_INVALID_TENANT", "tenant_id must be non-empty string", data)
    if not isinstance(operator_id, str) or not operator_id.strip():
        return _resp(False, "CONTEXT_INVALID_OPERATOR", "operator_id must be non-empty string", data)
    if not isinstance(task_id, str) or not task_id.strip():
        return _resp(False, "CONTEXT_INVALID_TASK", "task_id must be non-empty string", data)
    if not isinstance(payload, dict):
        return _resp(False, "CONTEXT_INVALID_PAYLOAD", "payload must be object", data)

    key = _tenant_operator_key(tenant_id.strip(), operator_id.strip())
    session_id = payload.get("session_id") if isinstance(payload.get("session_id"), str) else f"sess_{task_id.strip()}"
    record = {
        "session_id": session_id,
        "task_id": task_id.strip(),
        "payload": payload,
        "updated_at": _utc_now(),
    }
    _SESSION_STORE.setdefault(key, {})[session_id] = record

    summary = ""
    result = payload.get("result")
    if isinstance(result, dict):
        maybe_summary = result.get("summary")
        if isinstance(maybe_summary, str):
            summary = maybe_summary.strip()
    if summary:
        _MEMORY_STORE.append(
            {
                "tenant_id": tenant_id.strip(),
                "operator_id": operator_id.strip(),
                "task_id": task_id.strip(),
                "session_id": session_id,
                "summary": summary[:500],
                "created_at": _utc_now(),
            }
        )

    return _resp(True, "OK", "session saved", {"tenant_id": tenant_id, "operator_id": operator_id, "session_id": session_id})


def search_memory(tenant_id: str, query: str, top_k: int = 5) -> dict:
    data = {"tenant_id": tenant_id, "query": query, "top_k": top_k}

    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return _resp(False, "CONTEXT_INVALID_TENANT", "tenant_id must be non-empty string", data)
    if not isinstance(query, str) or not query.strip():
        return _resp(False, "CONTEXT_INVALID_QUERY", "query must be non-empty string", data)
    if not isinstance(top_k, int) or top_k <= 0:
        return _resp(False, "CONTEXT_INVALID_TOPK", "top_k must be positive integer", data)

    tenant = tenant_id.strip()
    terms = [t for t in query.strip().lower().split() if t]
    results = []
    for item in _MEMORY_STORE:
        if item.get("tenant_id") != tenant:
            continue
        summary = str(item.get("summary", "")).lower()
        score = sum(1 for t in terms if t in summary)
        if score > 0:
            results.append({**item, "score": score})

    results.sort(key=lambda x: (-x["score"], x.get("created_at", "")))
    return _resp(True, "OK", "memory search finished", {"tenant_id": tenant, "query": query, "hits": results[:top_k]})
