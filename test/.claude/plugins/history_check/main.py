"""History duplicate plugin MVP with unified response envelope."""

from __future__ import annotations

import json
from typing import Any, Dict, List


PLUGIN = "history_check"


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def _mock_hits(invoice_number: str, employee_id: str) -> List[dict]:
    hits: List[dict] = []
    if invoice_number.endswith(("88", "99")):
        hits.append(
            {
                "record_id": f"HX-{invoice_number}",
                "employee_id": employee_id,
                "invoice_number": invoice_number,
                "reason": "same invoice_number seen before",
            }
        )
    return hits


def run(tenant_id: str, invoice_number: str, employee_id: str) -> dict:
    data: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "invoice_number": invoice_number,
        "employee_id": employee_id,
    }

    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return _resp(False, "HISTORY_INVALID_TENANT", "tenant_id must be non-empty string", data)
    if not isinstance(employee_id, str) or not employee_id.strip():
        return _resp(False, "HISTORY_INVALID_EMPLOYEE", "employee_id must be non-empty string", data)
    if not isinstance(invoice_number, str) or not invoice_number.strip():
        return _resp(False, "HISTORY_INVALID_INVOICE_NUMBER", "invoice_number must be non-empty string", data)

    hits = _mock_hits(invoice_number, employee_id)
    data["hits"] = hits
    data["matched"] = bool(hits)
    data["dedup_key"] = f"{tenant_id}:{employee_id}:{invoice_number}"

    code = "OK" if not hits else "HISTORY_DUPLICATE_FOUND"
    message = "no duplicate found" if not hits else "duplicate found in history"
    return _resp(True, code, message, data)


if __name__ == "__main__":
    import sys

    try:
        args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
        if not isinstance(args, dict):
            args = {}
        result = run(
            tenant_id=args.get("tenant_id", ""),
            invoice_number=args.get("invoice_number", ""),
            employee_id=args.get("employee_id", ""),
        )
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:  # pragma: no cover
        print(
            json.dumps(
                _resp(False, "HISTORY_RUNTIME_ERROR", "history_check runtime error", {"error": str(exc)}),
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)
