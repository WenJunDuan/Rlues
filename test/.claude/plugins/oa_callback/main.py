"""OA callback plugin MVP with unified response envelope."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4


PLUGIN = "oa_callback"
ALLOWED_STATUS = {"completed", "needs_review", "failed", "timeout"}


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def run(task_id: str, status: str, summary: str) -> dict:
    data: Dict[str, Any] = {"task_id": task_id, "status": status, "summary": summary}

    if not isinstance(task_id, str) or not task_id.strip():
        return _resp(False, "OA_INVALID_TASK_ID", "task_id must be non-empty string", data)
    if not isinstance(status, str) or status not in ALLOWED_STATUS:
        return _resp(False, "OA_INVALID_STATUS", "status is invalid", {**data, "allowed": sorted(ALLOWED_STATUS)})
    if not isinstance(summary, str) or not summary.strip():
        return _resp(False, "OA_INVALID_SUMMARY", "summary must be non-empty string", data)

    callback_payload = {
        "task_id": task_id,
        "status": status,
        "summary": summary.strip()[:500],
        "callback_id": f"cb_{uuid4().hex[:12]}",
        "sent_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endpoint": "mock://oa/workflow/callback",
    }

    data.update(callback_payload)
    if status == "failed":
        return _resp(True, "OA_CALLBACK_ACCEPTED_WITH_ALERT", "callback accepted for failed task", data)
    return _resp(True, "OK", "callback accepted", data)


if __name__ == "__main__":
    import sys

    try:
        args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
        if not isinstance(args, dict):
            args = {}
        result = run(
            task_id=args.get("task_id", ""),
            status=args.get("status", ""),
            summary=args.get("summary", ""),
        )
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:  # pragma: no cover
        print(
            json.dumps(
                _resp(False, "OA_RUNTIME_ERROR", "oa_callback runtime error", {"error": str(exc)}),
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)
