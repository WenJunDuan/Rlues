"""Stop hook check for minimal result-envelope completeness."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List


SIGNAL_KEYS = {"task_id", "command", "status", "result"}
ALLOWED_STATUS = {"completed", "needs_review", "failed", "timeout"}
ALLOWED_DECISIONS = {"approved", "rejected", "needs_review"}


def _load_payload(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _block(message: str, details: List[dict]) -> int:
    print(json.dumps({"block": True, "message": message, "details": details}, ensure_ascii=False), file=sys.stderr)
    return 2


def _pass(message: str, checked: bool) -> int:
    print(json.dumps({"block": False, "message": message, "checked": checked}, ensure_ascii=False))
    return 0


def _is_result_candidate(payload: Dict[str, Any]) -> bool:
    matched = SIGNAL_KEYS.intersection(payload.keys())
    return len(matched) >= 2


def main() -> int:
    raw = sys.argv[1] if len(sys.argv) > 1 else os.getenv("LAST_OUTPUT", "")
    payload = _load_payload(raw if isinstance(raw, str) else "")
    if not isinstance(payload, dict):
        return _pass("result check skipped: no json payload", False)
    if not _is_result_candidate(payload):
        return _pass("result check skipped: payload does not look like ResultEnvelope", False)

    missing = [key for key in ("task_id", "command", "status", "result") if key not in payload]
    if missing:
        return _block("result envelope missing required fields", [{"path": key, "reason": "missing"} for key in missing])

    status = payload.get("status")
    if status not in ALLOWED_STATUS:
        return _block("invalid result status", [{"path": "status", "value": status, "allowed": sorted(ALLOWED_STATUS)}])

    result = payload.get("result")
    if not isinstance(result, dict):
        return _block("result must be object", [{"path": "result", "expected": "object", "actual": type(result).__name__}])

    decision = result.get("decision")
    if decision not in ALLOWED_DECISIONS:
        return _block(
            "invalid result.decision",
            [{"path": "result.decision", "value": decision, "allowed": sorted(ALLOWED_DECISIONS)}],
        )

    confidence = result.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        return _block(
            "result.confidence must be number",
            [{"path": "result.confidence", "expected": "number", "actual": type(confidence).__name__}],
        )

    summary = result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return _block("result.summary must be non-empty string", [{"path": "result.summary", "value": summary}])

    issues = result.get("issues")
    if not isinstance(issues, list):
        return _block("result.issues must be array", [{"path": "result.issues", "expected": "array", "actual": type(issues).__name__}])

    error_issue_paths: List[str] = []
    for idx, issue in enumerate(issues):
        if not isinstance(issue, dict):
            return _block(
                "result.issues entries must be objects",
                [{"path": f"result.issues[{idx}]", "expected": "object", "actual": type(issue).__name__}],
            )
        if str(issue.get("severity", "")).strip().lower() == "error":
            error_issue_paths.append(f"result.issues[{idx}].severity")

    if decision == "approved" and error_issue_paths:
        details: List[dict] = [{"path": "result.decision", "value": decision}]
        details.extend([{"path": path, "value": "error"} for path in error_issue_paths])
        return _block("business consistency failed: approved decision cannot contain error issues", details)

    return _pass("result check passed", True)


if __name__ == "__main__":
    raise SystemExit(main())
