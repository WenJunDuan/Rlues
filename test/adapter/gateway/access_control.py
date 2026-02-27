"""Gateway access control layer.

Encapsulates endpoint authorization and task ownership checks so route handlers
stay focused on HTTP transport wiring.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.api_server import get_task_meta
from ..core.error_codes import (
    ADAPTER_ENDPOINT_DISABLED,
    ADAPTER_FEATURE_DISABLED,
    ADAPTER_INSTRUCTION_MISMATCH,
    AUTH_CALLER_CONTEXT_MISMATCH,
    AUTH_CALLER_CONTEXT_MISSING,
    AUTH_INVALID_API_KEY,
    AUTH_MISSING_API_KEY,
    AUTH_TASK_ACCESS_DENIED,
    hash_api_key,
)
from . import http_access
from .response_mapper import failed_response

CALLER_TENANT_HEADER = "X-Tenant-Id"
CALLER_OPERATOR_HEADER = "X-Operator-Id"


def clean_header_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None



def is_internal_api_key(token: Optional[str]) -> bool:
    cleaned = clean_header_value(token)
    if cleaned is None:
        return False
    return cleaned in http_access.HTTP_ACCESS.internal_api_keys


def task_access_guard(
    *,
    task_id: str,
    api_key: Optional[str],
    caller_tenant_id: Optional[str],
    caller_operator_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    # Internal key is trusted for cross-task diagnostics.
    if is_internal_api_key(api_key):
        return None

    meta = get_task_meta(task_id)
    if meta is None:
        return None

    tenant = clean_header_value(caller_tenant_id)
    operator = clean_header_value(caller_operator_id)
    if tenant is None or operator is None:
        return failed_response(
            AUTH_CALLER_CONTEXT_MISSING,
            "missing caller context headers",
            task_id=task_id,
            details=[
                {"path": "header", "value": CALLER_TENANT_HEADER},
                {"path": "header", "value": CALLER_OPERATOR_HEADER},
            ],
            recoverable=True,
        )

    expected_tenant = str(meta.get("tenant_id", "")).strip()
    expected_operator = str(meta.get("operator_id", "")).strip()
    if tenant != expected_tenant or operator != expected_operator:
        return failed_response(
            AUTH_CALLER_CONTEXT_MISMATCH,
            "caller context does not match task owner",
            task_id=task_id,
            details=[
                {"path": "caller.tenant_id", "value": tenant},
                {"path": "caller.operator_id", "value": operator},
            ],
            recoverable=True,
        )

    owner_hash = str(meta.get("owner_api_key_hash", "")).strip()
    if owner_hash:
        caller_hash = hash_api_key(api_key)
        if caller_hash != owner_hash:
            return failed_response(
                AUTH_TASK_ACCESS_DENIED,
                "api key is not allowed to access this task",
                task_id=task_id,
                details=[{"path": "auth.key", "reason": "owner_mismatch"}],
                recoverable=True,
            )

    return None


def endpoint_access_guard(
    endpoint: str,
    *,
    api_key: Optional[str] = None,
    feature: Optional[str] = None,
    instruction: Optional[str] = None,
    task_id: str = "",
) -> Optional[Dict[str, Any]]:
    endpoint_policy = http_access.HTTP_ACCESS.endpoint_policy(endpoint)
    if not endpoint_policy.enabled:
        return failed_response(
            ADAPTER_ENDPOINT_DISABLED,
            f"endpoint disabled: {endpoint}",
            task_id=task_id,
            status="not_found",
            details=[{"path": "endpoint", "value": endpoint}],
            recoverable=True,
        )

    required_scope = endpoint_policy.scope
    if feature is not None:
        feature_policy = http_access.HTTP_ACCESS.feature_policy(feature)
        if feature_policy is None or not feature_policy.enabled or not feature_policy.expose_http:
            return failed_response(
                ADAPTER_FEATURE_DISABLED,
                f"feature not exposed: {feature}",
                task_id=task_id,
                status="not_found",
                details=[{"path": "feature", "value": feature}],
                recoverable=True,
            )
        if instruction is not None and instruction != feature_policy.instruction:
            return failed_response(
                ADAPTER_INSTRUCTION_MISMATCH,
                f"instruction mismatch for feature {feature}",
                task_id=task_id,
                status="not_found",
                details=[
                    {"path": "instruction", "value": instruction},
                    {"path": "expected_instruction", "value": feature_policy.instruction},
                ],
                recoverable=True,
            )
        if feature_policy.scope == http_access.INTERNAL_SCOPE:
            required_scope = http_access.INTERNAL_SCOPE

    authorized, reason = http_access.HTTP_ACCESS.authorize(required_scope, api_key)
    if authorized:
        return None

    code = AUTH_MISSING_API_KEY if "missing api key" in reason else AUTH_INVALID_API_KEY
    return failed_response(
        code,
        reason,
        task_id=task_id,
        details=[
            {"path": "auth.header", "value": http_access.HTTP_ACCESS.auth_header},
            {"path": "auth.scope", "value": required_scope},
        ],
        recoverable=True,
    )
