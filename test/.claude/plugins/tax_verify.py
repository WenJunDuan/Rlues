"""Tax verify plugin MVP with unified response envelope."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


PLUGIN = "tax_verify"


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def run(invoice_code: str, invoice_number: str, date: str, amount: float) -> dict:
    data: Dict[str, Any] = {
        "invoice_code": invoice_code,
        "invoice_number": invoice_number,
        "date": date,
        "amount": amount,
    }

    if not isinstance(invoice_code, str) or not invoice_code.strip():
        return _resp(False, "TAX_INVALID_INVOICE_CODE", "invoice_code must be non-empty string", data)
    if not isinstance(invoice_number, str) or not invoice_number.strip():
        return _resp(False, "TAX_INVALID_INVOICE_NUMBER", "invoice_number must be non-empty string", data)
    if not isinstance(amount, (int, float)) or isinstance(amount, bool) or float(amount) <= 0:
        return _resp(False, "TAX_INVALID_AMOUNT", "amount must be positive number", data)
    if not isinstance(date, str):
        return _resp(False, "TAX_INVALID_DATE", "date must be string in YYYY-MM-DD", data)

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return _resp(False, "TAX_INVALID_DATE", "date must match YYYY-MM-DD", data)

    issues = []
    status = "verified"
    matched = True

    if float(amount) > 10000:
        status = "needs_review"
        matched = False
        issues.append("amount exceeds auto-verify threshold")

    if invoice_code.startswith("0"):
        status = "needs_review"
        matched = False
        issues.append("invoice_code starts with 0, manual confirmation required")

    data.update(
        {
            "status": status,
            "matched": matched,
            "issues": issues,
            "verified_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "local-tax-mvp",
        }
    )

    code = "OK" if matched else "TAX_NEEDS_REVIEW"
    message = "tax verification passed" if matched else "tax verification needs review"
    return _resp(True, code, message, data)
