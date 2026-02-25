"""Context store plugin with file-backed persistence and unified response envelope."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


PLUGIN = "context_store"
DEFAULT_STORE_PATH = ".ai_state/runtime/context_store"


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def _safe_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value.strip())


def _store_dir() -> Path:
    path = os.environ.get("CONTEXT_STORE_PATH", DEFAULT_STORE_PATH)
    return Path(path).expanduser()


def _session_path(tenant_id: str, operator_id: str) -> Path:
    safe_tenant = _safe_token(tenant_id)
    safe_operator = _safe_token(operator_id)
    return _store_dir() / "sessions" / f"{safe_tenant}__{safe_operator}.json"


def _memory_path(tenant_id: str) -> Path:
    safe_tenant = _safe_token(tenant_id)
    return _store_dir() / "memory" / f"{safe_tenant}.jsonl"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _read_json_map(path: Path) -> Dict[str, dict]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            content = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(content, dict):
        return {}
    return {k: v for k, v in content.items() if isinstance(k, str) and isinstance(v, dict)}


def _atomic_write_json(path: Path, content: Dict[str, dict]) -> None:
    _ensure_parent(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(content, handle, ensure_ascii=False)
    temp.replace(path)


def _append_jsonl(path: Path, row: dict) -> None:
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []

    rows: List[dict] = []
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
                    rows.append(item)
    except OSError:
        return []
    return rows


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_session(tenant_id: str, operator_id: str, session_id: str | None = None) -> dict:
    data = {"tenant_id": tenant_id, "operator_id": operator_id, "session_id": session_id}

    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return _resp(False, "CONTEXT_INVALID_TENANT", "tenant_id must be non-empty string", data)
    if not isinstance(operator_id, str) or not operator_id.strip():
        return _resp(False, "CONTEXT_INVALID_OPERATOR", "operator_id must be non-empty string", data)

    tenant = tenant_id.strip()
    operator = operator_id.strip()
    path = _session_path(tenant, operator)
    sessions = _read_json_map(path)
    if not sessions:
        return _resp(True, "CONTEXT_NOT_FOUND", "session not found", {**data, "session": None})

    if session_id is not None:
        if not isinstance(session_id, str) or not session_id.strip():
            return _resp(False, "CONTEXT_INVALID_SESSION", "session_id must be non-empty string", data)
        target = session_id.strip()
        session = sessions.get(target)
        if session is None:
            return _resp(True, "CONTEXT_NOT_FOUND", "session_id not found", {**data, "session": None})
        return _resp(True, "OK", "session loaded", {"tenant_id": tenant, "operator_id": operator, "session_id": target, "session": session})

    latest = max(sessions.values(), key=lambda item: str(item.get("updated_at", "")))
    return _resp(True, "OK", "latest session loaded", {"tenant_id": tenant, "operator_id": operator, "session": latest})


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

    tenant = tenant_id.strip()
    operator = operator_id.strip()
    task = task_id.strip()

    raw_session = payload.get("session_id")
    if isinstance(raw_session, str) and raw_session.strip():
        session_id = raw_session.strip()
    else:
        session_id = f"sess_{task}"

    record = {
        "session_id": session_id,
        "task_id": task,
        "payload": payload,
        "updated_at": _utc_now(),
    }

    session_file = _session_path(tenant, operator)
    sessions = _read_json_map(session_file)
    sessions[session_id] = record
    _atomic_write_json(session_file, sessions)

    summary = ""
    result = payload.get("result")
    if isinstance(result, dict):
        maybe_summary = result.get("summary")
        if isinstance(maybe_summary, str):
            summary = maybe_summary.strip()
    if summary:
        memory_row = {
            "tenant_id": tenant,
            "operator_id": operator,
            "task_id": task,
            "session_id": session_id,
            "summary": summary[:500],
            "created_at": _utc_now(),
        }
        _append_jsonl(_memory_path(tenant), memory_row)

    return _resp(True, "OK", "session saved", {"tenant_id": tenant, "operator_id": operator, "session_id": session_id})


def search_memory(tenant_id: str, query: str, top_k: int = 5) -> dict:
    data = {"tenant_id": tenant_id, "query": query, "top_k": top_k}

    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return _resp(False, "CONTEXT_INVALID_TENANT", "tenant_id must be non-empty string", data)
    if not isinstance(query, str) or not query.strip():
        return _resp(False, "CONTEXT_INVALID_QUERY", "query must be non-empty string", data)
    if not isinstance(top_k, int) or top_k <= 0:
        return _resp(False, "CONTEXT_INVALID_TOPK", "top_k must be positive integer", data)

    tenant = tenant_id.strip()
    terms = [term for term in query.strip().lower().split() if term]
    rows = _read_jsonl(_memory_path(tenant))

    hits: List[dict] = []
    for item in rows:
        summary = str(item.get("summary", "")).lower()
        score = sum(1 for term in terms if term in summary)
        if score <= 0:
            continue
        hits.append({**item, "score": score})

    hits.sort(key=lambda item: (int(item["score"]), str(item.get("created_at", ""))), reverse=True)
    return _resp(True, "OK", "memory search finished", {"tenant_id": tenant, "query": query, "hits": hits[:top_k]})


def _parse_json_arg(raw: str | None) -> dict:
    text = (raw or "{}").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _arg_text(args: dict, key: str) -> str:
    value = args.get(key)
    return value if isinstance(value, str) else ""


def _cli() -> dict:
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    args = _parse_json_arg(sys.argv[2] if len(sys.argv) > 2 else "{}")

    if action == "load_session":
        return load_session(
            tenant_id=_arg_text(args, "tenant_id"),
            operator_id=_arg_text(args, "operator_id"),
            session_id=args.get("session_id"),
        )
    if action == "save_session":
        return save_session(
            tenant_id=_arg_text(args, "tenant_id"),
            operator_id=_arg_text(args, "operator_id"),
            task_id=_arg_text(args, "task_id"),
            payload=args.get("payload") if isinstance(args.get("payload"), dict) else {},
        )
    if action == "search_memory":
        raw_top_k = args.get("top_k", 5)
        top_k = raw_top_k if isinstance(raw_top_k, int) else 5
        return search_memory(
            tenant_id=_arg_text(args, "tenant_id"),
            query=_arg_text(args, "query"),
            top_k=top_k,
        )
    return _resp(False, "CONTEXT_INVALID_ACTION", "supported actions: load_session|save_session|search_memory", {"action": action})


if __name__ == "__main__":
    try:
        print(json.dumps(_cli(), ensure_ascii=False))
    except Exception as exc:  # pragma: no cover
        print(
            json.dumps(
                _resp(False, "CONTEXT_RUNTIME_ERROR", "context_store runtime error", {"error": str(exc)}),
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)
