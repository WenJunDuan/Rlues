"""OCR plugin MVP with unified response envelope."""

from __future__ import annotations

import os
import re
import json
from datetime import datetime
from typing import Any, Dict


PLUGIN = "ocr"
SUPPORTED_EXT = {".pdf", ".png", ".jpg", ".jpeg"}


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def _parse_filename(file_path: str) -> Dict[str, Any]:
    """
    Parse pattern:
    <invoice_code>_<invoice_number>_<YYYY-MM-DD>_<amount>_<category>.<ext>
    """
    name = os.path.basename(file_path)
    stem, _ext = os.path.splitext(name)
    parts = stem.split("_")
    if len(parts) < 5:
        return {"matched": False, "warnings": ["filename pattern not matched"]}

    invoice_code, invoice_number, date_text, amount_text, category = parts[:5]
    warnings = []

    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        warnings.append("invalid date in filename")

    amount: float | None = None
    try:
        amount = float(amount_text)
        if amount <= 0:
            warnings.append("amount should be positive")
    except ValueError:
        warnings.append("invalid amount in filename")

    if not re.fullmatch(r"\d{8,12}", invoice_number):
        warnings.append("invoice_number format unusual")
    if not re.fullmatch(r"\d{8,12}", invoice_code):
        warnings.append("invoice_code format unusual")

    return {
        "matched": True,
        "warnings": warnings,
        "structured": {
            "invoice_code": invoice_code,
            "invoice_number": invoice_number,
            "date": date_text,
            "amount": amount,
            "category": category.lower(),
            "currency": "CNY",
        },
    }


def run(file_path: str) -> dict:
    if not isinstance(file_path, str) or not file_path.strip():
        return _resp(False, "OCR_INVALID_INPUT", "file_path must be non-empty string", {"file_path": file_path})

    file_path = file_path.strip()
    _base, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext not in SUPPORTED_EXT:
        return _resp(
            False,
            "OCR_UNSUPPORTED_FILE_TYPE",
            "unsupported file extension",
            {"file_path": file_path, "supported": sorted(SUPPORTED_EXT)},
        )

    parsed = _parse_filename(file_path)
    data: Dict[str, Any] = {
        "file_path": file_path,
        "file_type": ext,
        "parser": "filename-mvp",
        "confidence_source": "simulated",
        "confidence": 0.6 if not parsed.get("matched") else 0.85,
    }

    if parsed.get("matched"):
        data["structured"] = parsed.get("structured", {})
        data["warnings"] = parsed.get("warnings", [])
        return _resp(True, "OK", "ocr parse finished", data)

    data["structured"] = {
        "invoice_code": "",
        "invoice_number": "",
        "date": "",
        "amount": None,
        "category": "unknown",
        "currency": "CNY",
    }
    data["warnings"] = parsed.get("warnings", ["unable to parse file name pattern"])
    return _resp(True, "OCR_PARTIAL_PARSE", "ocr parse finished with warnings", data)


if __name__ == "__main__":
    import sys

    try:
        args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
        if not isinstance(args, dict):
            args = {}
        result = run(file_path=args.get("file_path", ""))
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:  # pragma: no cover
        print(
            json.dumps(
                _resp(False, "OCR_RUNTIME_ERROR", "ocr runtime error", {"error": str(exc)}),
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)
