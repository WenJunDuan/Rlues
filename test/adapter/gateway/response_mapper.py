"""Gateway response helpers: error payload and HTTP status mapping."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.error_codes import (
    ADAPTER_ENDPOINT_DISABLED,
    ADAPTER_EXECUTION_ERROR,
    ADAPTER_FEATURE_DISABLED,
    ADAPTER_INSTRUCTION_MISMATCH,
    ADAPTER_PARSE_ERROR,
    AUTH_CALLER_CONTEXT_MISMATCH,
    AUTH_CALLER_CONTEXT_MISSING,
    AUTH_INVALID_API_KEY,
    AUTH_MISSING_API_KEY,
    AUTH_TASK_ACCESS_DENIED,
    SDK_EVENT_LOOP_ERROR,
    SDK_IMPORT_ERROR,
    SDK_OPTIONS_ERROR,
    SDK_QUERY_ERROR,
    SDK_RESULT_MAPPING_ERROR,
    VALIDATION_FAILED,
    VALIDATION_INVALID_VALUE,
    error_payload,
)


def is_duplicate_task_error(response: Dict[str, Any]) -> bool:
    error = response.get("error")
    if not isinstance(error, dict):
        return False
    if error.get("code") != VALIDATION_INVALID_VALUE:
        return False
    details = error.get("details")
    if not isinstance(details, list):
        return False
    for item in details:
        if isinstance(item, dict) and item.get("path") == "task_id" and item.get("reason") == "duplicate":
            return True
    return False


def error_code(response: Dict[str, Any]) -> str:
    error = response.get("error")
    return str(error.get("code", "")).strip() if isinstance(error, dict) else ""


def status_for_submit(response: Dict[str, Any]) -> int:
    status = str(response.get("status", "")).strip().lower()
    if status in {"processing", "queued"}:
        return 202
    if status == "not_found":
        return 404
    if status != "failed":
        return 200

    if is_duplicate_task_error(response):
        return 409

    code = error_code(response)
    if code in {
        AUTH_MISSING_API_KEY,
        AUTH_INVALID_API_KEY,
        AUTH_CALLER_CONTEXT_MISSING,
        AUTH_CALLER_CONTEXT_MISMATCH,
        AUTH_TASK_ACCESS_DENIED,
    }:
        return 403
    if code in {ADAPTER_ENDPOINT_DISABLED, ADAPTER_FEATURE_DISABLED, ADAPTER_INSTRUCTION_MISMATCH}:
        return 404
    if code in {VALIDATION_INVALID_VALUE, VALIDATION_FAILED, ADAPTER_PARSE_ERROR}:
        return 400
    if code in {
        SDK_IMPORT_ERROR,
        SDK_OPTIONS_ERROR,
        SDK_QUERY_ERROR,
        SDK_RESULT_MAPPING_ERROR,
        SDK_EVENT_LOOP_ERROR,
        ADAPTER_EXECUTION_ERROR,
    }:
        return 500
    return 400


def status_for_query(response: Dict[str, Any]) -> int:
    status = str(response.get("status", "")).strip().lower()
    if status in {"queued", "processing"}:
        return 202
    if status == "not_found":
        return 404
    if status == "failed":
        code = error_code(response)
        if code in {
            AUTH_MISSING_API_KEY,
            AUTH_INVALID_API_KEY,
            AUTH_CALLER_CONTEXT_MISSING,
            AUTH_CALLER_CONTEXT_MISMATCH,
            AUTH_TASK_ACCESS_DENIED,
        }:
            return 403
        if code in {ADAPTER_ENDPOINT_DISABLED, ADAPTER_FEATURE_DISABLED, ADAPTER_INSTRUCTION_MISMATCH}:
            return 404
        return 500
    return 200


def status_for_generic(response: Dict[str, Any]) -> int:
    status = str(response.get("status", "")).strip().lower()
    if status in {"ok", "deleted", "completed", "processing", "queued"}:
        return 200
    if status == "not_found":
        return 404
    if status == "failed":
        code = error_code(response)
        if code in {
            AUTH_MISSING_API_KEY,
            AUTH_INVALID_API_KEY,
            AUTH_CALLER_CONTEXT_MISSING,
            AUTH_CALLER_CONTEXT_MISMATCH,
            AUTH_TASK_ACCESS_DENIED,
        }:
            return 403
        if code in {ADAPTER_ENDPOINT_DISABLED, ADAPTER_FEATURE_DISABLED, ADAPTER_INSTRUCTION_MISMATCH}:
            return 404
        if code in {VALIDATION_INVALID_VALUE, VALIDATION_FAILED, ADAPTER_PARSE_ERROR}:
            return 400
        return 500
    return 200


def failed_response(
    code: str,
    message: str,
    *,
    task_id: str = "",
    status: str = "failed",
    details: Optional[list] = None,
    recoverable: bool = True,
) -> Dict[str, Any]:
    response: Dict[str, Any] = {
        "status": status,
        "error": error_payload(code, message, details=details, recoverable=recoverable),
    }
    if task_id:
        response["task_id"] = task_id
    return response
