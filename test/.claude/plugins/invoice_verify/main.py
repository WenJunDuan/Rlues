"""Invoice usage-check plugin with reserved internal API slot."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


PLUGIN = "invoice_verify"
SUPPORTED_CHANNELS = {"reserved", "mock", "external"}


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def run(
    tenant_id: str,
    invoice_code: str,
    invoice_number: str,
    date: str,
    amount: float,
    seller_tax_no: Optional[str] = None,
    channel: str = "reserved",
    verified: Optional[bool] = None,
    used_before: Optional[bool] = None,
) -> dict:
    data: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "invoice_code": invoice_code,
        "invoice_number": invoice_number,
        "date": date,
        "amount": amount,
        "seller_tax_no": seller_tax_no,
        "channel": channel,
        "verified": verified,
        "used_before": used_before,
    }

    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return _resp(False, "INVOICE_VERIFY_INVALID_TENANT", "tenant_id must be non-empty string", data)
    if not isinstance(invoice_code, str) or not invoice_code.strip():
        return _resp(False, "INVOICE_VERIFY_INVALID_CODE", "invoice_code must be non-empty string", data)
    if not isinstance(invoice_number, str) or not invoice_number.strip():
        return _resp(False, "INVOICE_VERIFY_INVALID_NUMBER", "invoice_number must be non-empty string", data)
    if not isinstance(date, str):
        return _resp(False, "INVOICE_VERIFY_INVALID_DATE", "date must be string in YYYY-MM-DD", data)
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return _resp(False, "INVOICE_VERIFY_INVALID_DATE", "date must match YYYY-MM-DD", data)
    if not isinstance(amount, (int, float)) or isinstance(amount, bool) or float(amount) <= 0:
        return _resp(False, "INVOICE_VERIFY_INVALID_AMOUNT", "amount must be positive number", data)
    if seller_tax_no is not None and (not isinstance(seller_tax_no, str) or not seller_tax_no.strip()):
        return _resp(False, "INVOICE_VERIFY_INVALID_TAX_NO", "seller_tax_no must be non-empty string", data)
    if channel not in SUPPORTED_CHANNELS:
        return _resp(False, "INVOICE_VERIFY_INVALID_CHANNEL", "channel must be reserved|mock|external", data)
    if verified is not None and not isinstance(verified, bool):
        return _resp(False, "INVOICE_VERIFY_INVALID_VERIFIED", "verified must be boolean when provided", data)
    if used_before is not None and not isinstance(used_before, bool):
        return _resp(False, "INVOICE_VERIFY_INVALID_USED_FLAG", "used_before must be boolean when provided", data)

    verify_id = f"invv_{uuid4().hex[:12]}"
    base = {
        **data,
        "verify_id": verify_id,
        "verify_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": "internal_usage_check",
    }
    if verified is not None:
        base["notes"] = ["verified parameter is deprecated in usage-check mode"]

    if channel == "reserved":
        reserved_used_before = False if used_before is None else used_before
        status = "clear" if not reserved_used_before else "used_before"
        code = "OK" if not reserved_used_before else "INVOICE_USED_BEFORE"
        message = "invoice usage check passed" if not reserved_used_before else "invoice has already been used"
        risk_tags = []
        if used_before is None:
            risk_tags.append("assumed_unused_without_internal_api")
        if reserved_used_before:
            risk_tags.append("used_before")
        base.update(
            {
                "status": status,
                "verified": not reserved_used_before,
                "used_before": reserved_used_before,
                "verify_source": "reserved-internal-usage-api",
                "risk_tags": risk_tags,
            }
        )
        return _resp(True, code, message, base)

    if channel == "external":
        ext_used_before = False if used_before is None else used_before
        final_verified = not ext_used_before
        risk_tags = []
        if ext_used_before:
            risk_tags.append("used_before")
        base.update(
            {
                "status": "clear" if final_verified else "used_before",
                "verified": final_verified,
                "used_before": ext_used_before,
                "verify_source": "external-internal-usage-api",
                "risk_tags": risk_tags,
            }
        )
        code = "OK" if final_verified else "INVOICE_USED_BEFORE"
        message = "invoice usage check passed" if final_verified else "invoice has already been used"
        return _resp(True, code, message, base)

    mock_used_before = invoice_number.strip().endswith(("88", "77"))
    final_verified = not mock_used_before
    risk_tags = []
    if mock_used_before:
        risk_tags.append("used_before")
    base.update(
        {
            "status": "clear" if final_verified else "used_before",
            "verified": final_verified,
            "used_before": mock_used_before,
            "verify_source": "local-usage-mock",
            "risk_tags": risk_tags,
        }
    )
    code = "OK" if final_verified else "INVOICE_USED_BEFORE"
    message = "invoice usage check passed" if final_verified else "invoice has already been used"
    return _resp(True, code, message, base)


if __name__ == "__main__":
    import sys

    try:
        args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
        if not isinstance(args, dict):
            args = {}
        result = run(
            tenant_id=args.get("tenant_id", ""),
            invoice_code=args.get("invoice_code", ""),
            invoice_number=args.get("invoice_number", ""),
            date=args.get("date", ""),
            amount=args.get("amount", 0),
            seller_tax_no=args.get("seller_tax_no"),
            channel=args.get("channel", "reserved"),
            verified=args.get("verified"),
            used_before=args.get("used_before"),
        )
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:  # pragma: no cover
        print(
            json.dumps(
                _resp(False, "INVOICE_VERIFY_RUNTIME_ERROR", "invoice_verify runtime error", {"error": str(exc)}),
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)
