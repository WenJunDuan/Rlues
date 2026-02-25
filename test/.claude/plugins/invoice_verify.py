"""Invoice authenticity verification plugin with reserved external API slot."""

from __future__ import annotations

from datetime import datetime
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
        "verify_time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    if channel == "reserved":
        base.update(
            {
                "status": "verified",
                "verified": True,
                "used_before": False,
                "verify_source": "reserved-external-api",
                "risk_tags": ["assumed_valid_without_external_api"],
            }
        )
        return _resp(
            True,
            "INVOICE_VERIFY_ASSUMED_VALID",
            "external invoice verification API not connected; assume invoice valid in first-gate mode",
            base,
        )

    if channel == "external":
        ext_verified = True if verified is None else verified
        ext_used_before = False if used_before is None else used_before
        final_verified = ext_verified and not ext_used_before
        risk_tags = []
        if ext_used_before:
            risk_tags.append("used_before")
        if not ext_verified:
            risk_tags.append("auth_failed")
        base.update(
            {
                "status": "verified" if final_verified else "fake_or_used",
                "verified": final_verified,
                "used_before": ext_used_before,
                "verify_source": "external-api",
                "risk_tags": risk_tags,
            }
        )
        code = "OK" if final_verified else "INVOICE_VERIFY_RISK"
        message = "invoice authenticity check passed" if final_verified else "invoice authenticity check found risk"
        return _resp(True, code, message, base)

    mock_verified = not invoice_number.strip().endswith(("98", "99"))
    mock_used_before = invoice_number.strip().endswith(("88", "77"))
    final_verified = mock_verified and not mock_used_before
    risk_tags = []
    if mock_used_before:
        risk_tags.append("used_before")
    if not mock_verified:
        risk_tags.append("mock_pattern_risk")
    base.update(
        {
            "status": "verified" if final_verified else "fake_or_used",
            "verified": final_verified,
            "used_before": mock_used_before,
            "verify_source": "local-mock",
            "risk_tags": risk_tags,
        }
    )
    code = "OK" if final_verified else "INVOICE_VERIFY_RISK"
    message = "invoice authenticity check passed" if final_verified else "invoice authenticity check found risk"
    return _resp(True, code, message, base)
