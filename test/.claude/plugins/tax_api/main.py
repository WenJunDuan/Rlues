"""Tax authority API query plugin — pure I/O, no business judgment.

Calls an external tax verification API and returns the raw result.
All business rules (amount thresholds, compliance checks) belong in
skill rules, not here.

Usage:
    python3 .claude/plugins/tax_api/main.py '{"invoice_code":"3100...","invoice_number":"12345678","invoice_date":"2026-01-15","amount":"8500.00"}'

Output: JSON envelope with tax authority raw response in ``data``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


PLUGIN = "tax_api"


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def run(
    invoice_code: str,
    invoice_number: str,
    invoice_date: str,
    amount: float,
) -> dict:
    """Call tax authority API and return raw verification result.

    This plugin performs **no** business judgment.  It only relays the
    external service response so that downstream skill rules can reason
    about it.
    """
    data: Dict[str, Any] = {
        "invoice_code": invoice_code,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "amount": amount,
    }

    # --- input validation (structural only, not business rules) ---
    if not isinstance(invoice_code, str) or not invoice_code.strip():
        return _resp(False, "TAX_API_INVALID_INVOICE_CODE", "invoice_code must be non-empty string", data)
    if not isinstance(invoice_number, str) or not invoice_number.strip():
        return _resp(False, "TAX_API_INVALID_INVOICE_NUMBER", "invoice_number must be non-empty string", data)
    if not isinstance(amount, (int, float)) or isinstance(amount, bool) or float(amount) <= 0:
        return _resp(False, "TAX_API_INVALID_AMOUNT", "amount must be positive number", data)
    if not isinstance(invoice_date, str):
        return _resp(False, "TAX_API_INVALID_DATE", "invoice_date must be string in YYYY-MM-DD", data)
    try:
        datetime.strptime(invoice_date, "%Y-%m-%d")
    except ValueError:
        return _resp(False, "TAX_API_INVALID_DATE", "invoice_date must match YYYY-MM-DD", data)

    # --- external API call ---
    api_url = os.getenv("TAX_API_URL", "")
    api_key = os.getenv("TAX_API_KEY", "")

    if not api_url or not api_key:
        # When API is not configured, return a structured "unconfigured" result
        # so skill rules can handle this gracefully.
        data.update({
            "status": "unconfigured",
            "raw_response": None,
            "source": "tax-api-plugin",
            "queried_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        return _resp(True, "TAX_API_NOT_CONFIGURED", "tax authority API not configured", data)

    try:
        import requests  # lazy import — only needed when API is configured
        resp = requests.post(
            api_url,
            json={
                "invoiceCode": invoice_code,
                "invoiceNumber": invoice_number,
                "invoiceDate": invoice_date,
                "totalAmount": str(amount),
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        raw = resp.json()

        data.update({
            "status": "ok",
            "raw_response": raw,
            "source": "tax-authority-api",
            "queried_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        return _resp(True, "OK", "tax authority query completed", data)

    except Exception as exc:
        error_type = type(exc).__name__
        data.update({
            "status": "error",
            "raw_response": None,
            "error_type": error_type,
            "error_detail": str(exc),
            "source": "tax-api-plugin",
            "queried_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        return _resp(True, "TAX_API_QUERY_ERROR", f"tax authority query failed: {error_type}", data)


if __name__ == "__main__":
    import sys

    try:
        args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
        if not isinstance(args, dict):
            args = {}
        result = run(
            invoice_code=args.get("invoice_code", ""),
            invoice_number=args.get("invoice_number", ""),
            invoice_date=args.get("invoice_date", args.get("date", "")),
            amount=args.get("amount", 0),
        )
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:  # pragma: no cover
        print(
            json.dumps(
                _resp(False, "TAX_API_RUNTIME_ERROR", "tax_api runtime error", {"error": str(exc)}),
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)
