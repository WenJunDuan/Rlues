"""Standard query plugin MVP with unified response envelope."""

from __future__ import annotations

import json
from typing import Any, Dict, List


PLUGIN = "standard_query"
LEVEL_LIMITS = {"L1": 500.0, "L2": 1200.0, "L3": 2000.0, "L4": 3500.0}
DEPT_CATEGORIES = {
    "finance": ["transport", "hotel", "meal", "office"],
    "sales": ["transport", "hotel", "meal", "client"],
    "hr": ["transport", "hotel", "meal", "training"],
}


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def _normalize_department(department: str) -> str:
    return department.strip().lower()


def _normalize_level(level: str) -> str:
    return level.strip().upper()


def run(tenant_id: str, department: str, level: str, category: str, city: str | None = None) -> dict:
    data: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "department": department,
        "level": level,
        "category": category,
        "city": city,
    }

    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return _resp(False, "STANDARD_INVALID_TENANT", "tenant_id must be non-empty string", data)
    if not isinstance(department, str) or not department.strip():
        return _resp(False, "STANDARD_INVALID_DEPARTMENT", "department must be non-empty string", data)
    if not isinstance(level, str) or not level.strip():
        return _resp(False, "STANDARD_INVALID_LEVEL", "level must be non-empty string", data)
    if not isinstance(category, str) or not category.strip():
        return _resp(False, "STANDARD_INVALID_CATEGORY", "category must be non-empty string", data)

    department_key = _normalize_department(department)
    level_key = _normalize_level(level)
    category_key = category.strip().lower()

    limit = LEVEL_LIMITS.get(level_key, 800.0)
    allowed_categories: List[str] = DEPT_CATEGORIES.get(department_key, ["transport", "hotel", "meal"])
    category_allowed = category_key in allowed_categories

    warnings = []
    if level_key not in LEVEL_LIMITS:
        warnings.append("unknown level, fallback limit applied")
    if department_key not in DEPT_CATEGORIES:
        warnings.append("unknown department, fallback category set applied")
    if not category_allowed:
        warnings.append("category not in allowed set")

    data.update(
        {
            "limit": limit,
            "allowed_categories": allowed_categories,
            "category_allowed": category_allowed,
            "policy_version": "expense-policy-v4-mvp",
            "warnings": warnings,
        }
    )

    code = "OK" if category_allowed else "STANDARD_CATEGORY_REVIEW"
    message = "policy matched" if category_allowed else "policy check completed with category warning"
    return _resp(True, code, message, data)


if __name__ == "__main__":
    import sys

    try:
        args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
        if not isinstance(args, dict):
            args = {}
        result = run(
            tenant_id=args.get("tenant_id", ""),
            department=args.get("department", ""),
            level=args.get("level", ""),
            category=args.get("category", ""),
            city=args.get("city"),
        )
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:  # pragma: no cover
        print(
            json.dumps(
                _resp(False, "STANDARD_RUNTIME_ERROR", "standard_query runtime error", {"error": str(exc)}),
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)
