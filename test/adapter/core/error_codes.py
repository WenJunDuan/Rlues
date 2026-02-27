"""Centralized error code definitions for adapter and SDK bridge."""

import hashlib
from typing import Optional

# Validation layer
VALIDATION_FAILED = "VALIDATION_FAILED"
VALIDATION_MISSING_FIELD = "VALIDATION_MISSING_FIELD"
VALIDATION_TYPE_MISMATCH = "VALIDATION_TYPE_MISMATCH"
VALIDATION_INVALID_VALUE = "VALIDATION_INVALID_VALUE"

# Adapter layer
ADAPTER_PARSE_ERROR = "ADAPTER_PARSE_ERROR"
ADAPTER_TASK_NOT_FOUND = "ADAPTER_TASK_NOT_FOUND"
ADAPTER_STREAM_NOT_FOUND = "ADAPTER_STREAM_NOT_FOUND"
ADAPTER_EXECUTION_ERROR = "ADAPTER_EXECUTION_ERROR"

# SDK bridge layer
SDK_IMPORT_ERROR = "SDK_IMPORT_ERROR"
SDK_OPTIONS_ERROR = "SDK_OPTIONS_ERROR"
SDK_QUERY_ERROR = "SDK_QUERY_ERROR"
SDK_EVENT_LOOP_ERROR = "SDK_EVENT_LOOP_ERROR"
SDK_RESULT_MAPPING_ERROR = "SDK_RESULT_MAPPING_ERROR"

# HTTP access control layer
AUTH_MISSING_API_KEY = "AUTH_MISSING_API_KEY"
AUTH_INVALID_API_KEY = "AUTH_INVALID_API_KEY"
AUTH_CALLER_CONTEXT_MISSING = "AUTH_CALLER_CONTEXT_MISSING"
AUTH_CALLER_CONTEXT_MISMATCH = "AUTH_CALLER_CONTEXT_MISMATCH"
AUTH_TASK_ACCESS_DENIED = "AUTH_TASK_ACCESS_DENIED"
ADAPTER_ENDPOINT_DISABLED = "ADAPTER_ENDPOINT_DISABLED"
ADAPTER_FEATURE_DISABLED = "ADAPTER_FEATURE_DISABLED"
ADAPTER_INSTRUCTION_MISMATCH = "ADAPTER_INSTRUCTION_MISMATCH"


def error_payload(code: str, message: str, details: list | None = None, recoverable: bool = True) -> dict:
    payload = {
        "code": code,
        "message": message,
        "recoverable": recoverable,
    }
    if details:
        payload["details"] = details
    return payload


def hash_api_key(token: Optional[str]) -> Optional[str]:
    """SHA-256 hash of an API key for ownership comparison."""
    if not isinstance(token, str):
        return None
    value = token.strip()
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
