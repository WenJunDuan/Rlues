"""History duplicate plugin MVP with unified response envelope."""

from __future__ import annotations

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
