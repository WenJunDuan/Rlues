"""Gateway feature adaptation layer.

Converts feature-style API requests into core task envelope calls.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from ..core.api_server import get_result, submit_task
from ..core.error_codes import (
    ADAPTER_FEATURE_DISABLED,
    ADAPTER_INSTRUCTION_MISMATCH,
    AUTH_CALLER_CONTEXT_MISMATCH,
    AUTH_CALLER_CONTEXT_MISSING,
    VALIDATION_INVALID_VALUE,
)
from .access_control import (
    CALLER_OPERATOR_HEADER,
    CALLER_TENANT_HEADER,
    clean_header_value,
    is_internal_api_key,
)
from . import http_access
from .response_mapper import failed_response, status_for_query


def build_envelope(command: str, body: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if not isinstance(body, dict):
        return None, failed_response(VALIDATION_INVALID_VALUE, "request body must be object")

    has_envelope_shape = {"task_id", "context", "payload"}.issubset(set(body.keys()))
    if has_envelope_shape:
        envelope = dict(body)
        envelope["command"] = command
        return envelope, None

    envelope = {
        "task_id": str(body.get("task_id") or f"task_{uuid4().hex}"),
        "command": command,
        "context": body.get("context"),
        "payload": body.get("payload", body),
    }
    if "runtime" in body and body["runtime"] is not None:
        envelope["runtime"] = body["runtime"]
    return envelope, None


def feature_command(feature: str) -> Optional[str]:
    policy = http_access.HTTP_ACCESS.feature_policy(feature)
    if policy is None:
        return None
    return policy.command


def submit_feature_command(
    feature: str,
    body: Dict[str, Any],
    *,
    api_key: Optional[str],
    caller_tenant_id: Optional[str],
    caller_operator_id: Optional[str],
    instruction: Optional[str] = None,
) -> Dict[str, Any]:
    policy = http_access.HTTP_ACCESS.feature_policy(feature)
    if policy is None or not policy.enabled or not policy.expose_http:
        return failed_response(
            ADAPTER_FEATURE_DISABLED,
            f"feature not exposed: {feature}",
            status="not_found",
            details=[{"path": "feature", "value": feature}],
            recoverable=True,
        )
    if instruction is not None and instruction != policy.instruction:
        return failed_response(
            ADAPTER_INSTRUCTION_MISMATCH,
            f"instruction mismatch for feature {feature}",
            status="not_found",
            details=[
                {"path": "instruction", "value": instruction},
                {"path": "expected_instruction", "value": policy.instruction},
            ],
            recoverable=True,
        )

    envelope, error = build_envelope(policy.command, body)
    if error is not None:
        return error

    if not is_internal_api_key(api_key):
        tenant = clean_header_value(caller_tenant_id)
        operator = clean_header_value(caller_operator_id)
        if tenant is None or operator is None:
            return failed_response(
                AUTH_CALLER_CONTEXT_MISSING,
                "missing caller context headers",
                details=[
                    {"path": "header", "value": CALLER_TENANT_HEADER},
                    {"path": "header", "value": CALLER_OPERATOR_HEADER},
                ],
                recoverable=True,
            )

        context = envelope.get("context") if envelope is not None else None
        if not isinstance(context, dict):
            return failed_response(
                AUTH_CALLER_CONTEXT_MISMATCH,
                "task context missing for ownership binding",
                details=[{"path": "context", "reason": "missing_or_invalid"}],
                recoverable=True,
            )

        if str(context.get("tenant_id", "")).strip() != tenant or str(context.get("operator_id", "")).strip() != operator:
            return failed_response(
                AUTH_CALLER_CONTEXT_MISMATCH,
                "caller context does not match submitted task context",
                details=[
                    {"path": "caller.tenant_id", "value": tenant},
                    {"path": "caller.operator_id", "value": operator},
                ],
                recoverable=True,
            )

    return submit_task(envelope or {}, owner_api_key=api_key)


def check_task_feature_match(feature: str, task_id: str) -> Tuple[Dict[str, Any], int]:
    command = feature_command(feature)
    if command is None:
        response = failed_response(
            ADAPTER_FEATURE_DISABLED,
            f"unsupported feature: {feature}",
            task_id=task_id,
            status="not_found",
            details=[{"path": "feature", "value": feature}],
            recoverable=True,
        )
        return response, 404

    result = get_result(task_id)
    status_code = status_for_query(result)
    if status_code != 200:
        return result, status_code

    if result.get("command") != command:
        response = failed_response(
            VALIDATION_INVALID_VALUE,
            f"task command mismatch, expected {command}, got {result.get('command')}",
            task_id=task_id,
            details=[{"path": "task.command", "expected": command, "actual": result.get("command")}],
            recoverable=True,
        )
        return response, 409

    return result, 200
