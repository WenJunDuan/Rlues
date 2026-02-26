"""Context store plugin with file-backed persistence and layered memory."""

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
MAX_SUMMARY_LEN = 500
MAX_LINE_LEN = 300
SEVERITY_PRIORITY = {"error": 3, "warning": 2, "info": 1}


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def _safe_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value.strip())


def _store_dir() -> Path:
    path = os.environ.get("CONTEXT_STORE_PATH", DEFAULT_STORE_PATH)
    return Path(path).expanduser()


def _memory_dir() -> Path:
    return _store_dir() / "memory"


def _memory_index_path() -> Path:
    return _store_dir() / "MEMORY.md"


def _projects_path() -> Path:
    return _memory_dir() / "projects.md"


def _infra_path() -> Path:
    return _memory_dir() / "infra.md"


def _lessons_path() -> Path:
    return _memory_dir() / "lessons.md"


def _daily_path(day: str) -> Path:
    return _memory_dir() / f"{day}.md"


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


def _atomic_write_text(path: Path, content: str) -> None:
    _ensure_parent(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        handle.write(content)
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


def _ensure_markdown_file(path: Path, title: str) -> None:
    if path.exists():
        return
    _atomic_write_text(path, f"# {title}\n\n")


def _append_markdown_line(path: Path, title: str, line: str) -> None:
    _ensure_markdown_file(path, title)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _one_line(value: Any, max_len: int = MAX_LINE_LEN) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _extract_summary(payload: Dict[str, Any]) -> str:
    result = payload.get("result")
    if not isinstance(result, dict):
        return ""
    summary = result.get("summary")
    if not isinstance(summary, str):
        return ""
    return summary.strip()[:MAX_SUMMARY_LEN]


def _extract_decision(payload: Dict[str, Any]) -> str:
    result = payload.get("result")
    if not isinstance(result, dict):
        return "unknown"
    decision = result.get("decision")
    if not isinstance(decision, str) or not decision.strip():
        return "unknown"
    return decision.strip().lower()


def _extract_severity(payload: Dict[str, Any]) -> str:
    result = payload.get("result")
    if not isinstance(result, dict):
        return "info"
    issues = result.get("issues")
    if not isinstance(issues, list):
        return "info"

    best = "info"
    best_score = SEVERITY_PRIORITY[best]
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        level = str(issue.get("severity", "")).strip().lower()
        score = SEVERITY_PRIORITY.get(level)
        if score is None:
            continue
        if score > best_score:
            best = level
            best_score = score
    return best


def _infer_project(payload: Dict[str, Any], tenant_id: str) -> str:
    for key in ("project_id", "project", "project_name", "domain"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    context = payload.get("context")
    if isinstance(context, dict):
        for key in ("project_id", "project", "project_name"):
            value = context.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return tenant_id


def _refresh_infra_layer() -> None:
    root = _store_dir()
    lines = [
        "# Infrastructure Memory",
        "",
        "- Context store root: `" + str(root) + "`",
        "- Session store: `sessions/<tenant>__<operator>.json`",
        "- Search index: `memory/<tenant>.jsonl`",
        "- Layered memory index: `MEMORY.md`",
        "- Layered memory files: `memory/projects.md`, `memory/infra.md`, `memory/lessons.md`, `memory/YYYY-MM-DD.md`",
        "- Last refresh (UTC): `" + _utc_now() + "`",
        "",
    ]
    _atomic_write_text(_infra_path(), "\n".join(lines))


def _refresh_memory_index(latest: Dict[str, str]) -> None:
    lines = [
        "# MEMORY Index",
        "",
        "只放核心信息和索引，详细内容在 `memory/` 目录。",
        "",
        "## Layers",
        "- `memory/projects.md`: 项目层（当前状态与待办）",
        "- `memory/infra.md`: 基础设施层（配置与地址速查）",
        "- `memory/lessons.md`: 教训层（按严重级别沉淀）",
        "- `memory/" + latest["day"] + ".md`: 日志层（当日事件）",
        "",
        "## Latest",
        "- Updated (UTC): `" + latest["updated_at"] + "`",
        "- Tenant: `" + latest["tenant_id"] + "`",
        "- Operator: `" + latest["operator_id"] + "`",
        "- Project: `" + latest["project"] + "`",
        "- Task: `" + latest["task_id"] + "`",
        "- Session: `" + latest["session_id"] + "`",
        "- Decision: `" + latest["decision"] + "`",
        "",
    ]
    _atomic_write_text(_memory_index_path(), "\n".join(lines))


def _write_layered_memory(
    *,
    tenant_id: str,
    operator_id: str,
    task_id: str,
    session_id: str,
    payload: Dict[str, Any],
    summary: str,
) -> int:
    now = _utc_now()
    day = _utc_day()
    decision = _extract_decision(payload)
    severity = _extract_severity(payload)
    project = _infer_project(payload, tenant_id)
    summary_text = _one_line(summary or "(no summary)", max_len=MAX_SUMMARY_LEN)

    _refresh_infra_layer()

    project_line = (
        f"- [{now}] project=`{_one_line(project, 80)}` tenant=`{tenant_id}` operator=`{operator_id}` "
        f"task=`{task_id}` session=`{session_id}` decision=`{decision}` summary={summary_text}"
    )
    _append_markdown_line(_projects_path(), "Projects Memory", project_line)

    daily_line = (
        f"- [{now}] tenant=`{tenant_id}` operator=`{operator_id}` task=`{task_id}` "
        f"session=`{session_id}` decision=`{decision}` severity=`{severity}` summary={summary_text}"
    )
    _append_markdown_line(_daily_path(day), f"Daily Log {day}", daily_line)

    lesson_written = 0
    if decision in {"rejected", "needs_review"} or severity in {"error", "warning"}:
        lesson_line = (
            f"- [{now}] severity=`{severity}` tenant=`{tenant_id}` task=`{task_id}` "
            f"decision=`{decision}` lesson={summary_text}"
        )
        _append_markdown_line(_lessons_path(), "Lessons Memory", lesson_line)
        lesson_written = 1

    _refresh_memory_index(
        {
            "updated_at": now,
            "day": day,
            "tenant_id": tenant_id,
            "operator_id": operator_id,
            "project": _one_line(project, 80),
            "task_id": task_id,
            "session_id": session_id,
            "decision": decision,
        }
    )

    return 4 + lesson_written


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

    summary = _extract_summary(payload)
    if summary:
        memory_row = {
            "tenant_id": tenant,
            "operator_id": operator,
            "task_id": task,
            "session_id": session_id,
            "summary": summary,
            "created_at": _utc_now(),
        }
        _append_jsonl(_memory_path(tenant), memory_row)

    memory_items = _write_layered_memory(
        tenant_id=tenant,
        operator_id=operator,
        task_id=task,
        session_id=session_id,
        payload=payload,
        summary=summary,
    )

    return _resp(
        True,
        "OK",
        "session saved",
        {
            "tenant_id": tenant,
            "operator_id": operator,
            "session_id": session_id,
            "memory_items": memory_items,
        },
    )


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
