"""FastAPI HTTP server for adapter plane."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from ..core.api_server import (
    archive_logs,
    delete_history,
    get_compliance_feedback,
    get_task_meta,
    get_result,
    list_history,
    list_logs,
    queue_runtime,
    stream_events,
    submit_task,
)
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
from .http_access import HTTP_ACCESS, INTERNAL_SCOPE
from ..sdk.access import SDK_ACCESS

CALLER_TENANT_HEADER = "X-Tenant-Id"
CALLER_OPERATOR_HEADER = "X-Operator-Id"


def _is_duplicate_task_error(response: Dict[str, Any]) -> bool:
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


def _error_code(response: Dict[str, Any]) -> str:
    error = response.get("error")
    return str(error.get("code", "")).strip() if isinstance(error, dict) else ""


def _status_for_submit(response: Dict[str, Any]) -> int:
    status = str(response.get("status", "")).strip().lower()
    if status in {"processing", "queued"}:
        return 202
    if status == "not_found":
        return 404
    if status != "failed":
        return 200

    if _is_duplicate_task_error(response):
        return 409

    code = _error_code(response)
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


def _status_for_query(response: Dict[str, Any]) -> int:
    status = str(response.get("status", "")).strip().lower()
    if status in {"queued", "processing"}:
        return 202
    if status == "not_found":
        return 404
    if status == "failed":
        code = _error_code(response)
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


def _status_for_generic(response: Dict[str, Any]) -> int:
    status = str(response.get("status", "")).strip().lower()
    if status in {"ok", "deleted", "completed", "processing", "queued"}:
        return 200
    if status == "not_found":
        return 404
    if status == "failed":
        code = _error_code(response)
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


def _failed(
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


def _build_envelope(command: str, body: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if not isinstance(body, dict):
        return None, _failed(VALIDATION_INVALID_VALUE, "request body must be object")

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


def _feature_command(feature: str) -> Optional[str]:
    policy = HTTP_ACCESS.feature_policy(feature)
    if policy is None:
        return None
    return policy.command


def _clean_header_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _hash_api_key(token: Optional[str]) -> Optional[str]:
    cleaned = _clean_header_value(token)
    if cleaned is None:
        return None
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def _is_internal_api_key(token: Optional[str]) -> bool:
    cleaned = _clean_header_value(token)
    if cleaned is None:
        return False
    return cleaned in HTTP_ACCESS.internal_api_keys


def _task_access_guard(
    *,
    task_id: str,
    api_key: Optional[str],
    caller_tenant_id: Optional[str],
    caller_operator_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    # Internal key is trusted for cross-task diagnostics.
    if _is_internal_api_key(api_key):
        return None

    meta = get_task_meta(task_id)
    if meta is None:
        return None

    tenant = _clean_header_value(caller_tenant_id)
    operator = _clean_header_value(caller_operator_id)
    if tenant is None or operator is None:
        return _failed(
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
        return _failed(
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
        caller_hash = _hash_api_key(api_key)
        if caller_hash != owner_hash:
            return _failed(
                AUTH_TASK_ACCESS_DENIED,
                "api key is not allowed to access this task",
                task_id=task_id,
                details=[{"path": "auth.key", "reason": "owner_mismatch"}],
                recoverable=True,
            )
    return None


def _submit_feature_command(
    feature: str,
    body: Dict[str, Any],
    *,
    api_key: Optional[str],
    caller_tenant_id: Optional[str],
    caller_operator_id: Optional[str],
    instruction: Optional[str] = None,
) -> Dict[str, Any]:
    policy = HTTP_ACCESS.feature_policy(feature)
    if policy is None or not policy.enabled or not policy.expose_http:
        return _failed(
            ADAPTER_FEATURE_DISABLED,
            f"feature not exposed: {feature}",
            status="not_found",
            details=[{"path": "feature", "value": feature}],
            recoverable=True,
        )
    if instruction is not None and instruction != policy.instruction:
        return _failed(
            ADAPTER_INSTRUCTION_MISMATCH,
            f"instruction mismatch for feature {feature}",
            status="not_found",
            details=[
                {"path": "instruction", "value": instruction},
                {"path": "expected_instruction", "value": policy.instruction},
            ],
            recoverable=True,
        )

    envelope, error = _build_envelope(policy.command, body)
    if error is not None:
        return error

    if not _is_internal_api_key(api_key):
        tenant = _clean_header_value(caller_tenant_id)
        operator = _clean_header_value(caller_operator_id)
        if tenant is None or operator is None:
            return _failed(
                AUTH_CALLER_CONTEXT_MISSING,
                "missing caller context headers",
                details=[
                    {"path": "header", "value": CALLER_TENANT_HEADER},
                    {"path": "header", "value": CALLER_OPERATOR_HEADER},
                ],
                recoverable=True,
            )
        context = envelope.get("context")
        if not isinstance(context, dict):
            return _failed(
                AUTH_CALLER_CONTEXT_MISMATCH,
                "task context missing for ownership binding",
                details=[{"path": "context", "reason": "missing_or_invalid"}],
                recoverable=True,
            )
        if str(context.get("tenant_id", "")).strip() != tenant or str(context.get("operator_id", "")).strip() != operator:
            return _failed(
                AUTH_CALLER_CONTEXT_MISMATCH,
                "caller context does not match submitted task context",
                details=[
                    {"path": "caller.tenant_id", "value": tenant},
                    {"path": "caller.operator_id", "value": operator},
                ],
                recoverable=True,
            )

    return submit_task(envelope or {}, owner_api_key=api_key)


def _check_task_feature_match(feature: str, task_id: str) -> Tuple[Dict[str, Any], int]:
    command = _feature_command(feature)
    if command is None:
        response = _failed(
            ADAPTER_FEATURE_DISABLED,
            f"unsupported feature: {feature}",
            task_id=task_id,
            status="not_found",
            details=[{"path": "feature", "value": feature}],
            recoverable=True,
        )
        return response, 404

    result = get_result(task_id)
    status_code = _status_for_query(result)
    if status_code != 200:
        return result, status_code

    if result.get("command") != command:
        response = _failed(
            VALIDATION_INVALID_VALUE,
            f"task command mismatch, expected {command}, got {result.get('command')}",
            task_id=task_id,
            details=[{"path": "task.command", "expected": command, "actual": result.get("command")}],
            recoverable=True,
        )
        return response, 409
    return result, 200


def _access_guard(
    endpoint: str,
    *,
    api_key: Optional[str] = None,
    feature: Optional[str] = None,
    instruction: Optional[str] = None,
    task_id: str = "",
) -> Optional[Dict[str, Any]]:
    endpoint_policy = HTTP_ACCESS.endpoint_policy(endpoint)
    if not endpoint_policy.enabled:
        return _failed(
            ADAPTER_ENDPOINT_DISABLED,
            f"endpoint disabled: {endpoint}",
            task_id=task_id,
            status="not_found",
            details=[{"path": "endpoint", "value": endpoint}],
            recoverable=True,
        )

    feature_policy = None
    required_scope = endpoint_policy.scope
    if feature is not None:
        feature_policy = HTTP_ACCESS.feature_policy(feature)
        if feature_policy is None or not feature_policy.enabled or not feature_policy.expose_http:
            return _failed(
                ADAPTER_FEATURE_DISABLED,
                f"feature not exposed: {feature}",
                task_id=task_id,
                status="not_found",
                details=[{"path": "feature", "value": feature}],
                recoverable=True,
            )
        if instruction is not None and instruction != feature_policy.instruction:
            return _failed(
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
        if feature_policy.scope == INTERNAL_SCOPE:
            required_scope = INTERNAL_SCOPE

    authorized, reason = HTTP_ACCESS.authorize(required_scope, api_key)
    if authorized:
        return None

    code = AUTH_MISSING_API_KEY if "missing api key" in reason else AUTH_INVALID_API_KEY
    return _failed(
        code,
        reason,
        task_id=task_id,
        details=[
            {"path": "auth.header", "value": HTTP_ACCESS.auth_header},
            {"path": "auth.scope", "value": required_scope},
        ],
        recoverable=True,
    )


def create_app():
    """Build FastAPI app lazily so module import does not require FastAPI."""
    try:
        from fastapi import Body, FastAPI, Header, Query
        from fastapi.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("FastAPI server requires `fastapi` and `uvicorn` to be installed.") from exc

    app = FastAPI(
        title="Audit Adapter API",
        version="0.4.0",
        description="HTTP wrapper for adapter task submission and retrieval.",
    )

    @app.get("/health")
    async def health(api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header)) -> Dict[str, str]:
        guard = _access_guard("health", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=_status_for_generic(guard), content=guard)
        return {"status": "ok"}

    @app.post("/api/{feature}")
    async def post_api_feature(
        feature: str,
        payload: Dict[str, Any] = Body(...),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("feature_submit", api_key=api_key, feature=feature)
        if guard is not None:
            return JSONResponse(status_code=_status_for_submit(guard), content=guard)
        response = _submit_feature_command(
            feature,
            payload,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        return JSONResponse(status_code=_status_for_submit(response), content=response)

    @app.post("/api/{feature}/{instruction}")
    async def post_api_feature_instruction(
        feature: str,
        instruction: str,
        payload: Dict[str, Any] = Body(...),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("feature_submit", api_key=api_key, feature=feature, instruction=instruction)
        if guard is not None:
            return JSONResponse(status_code=_status_for_submit(guard), content=guard)
        response = _submit_feature_command(
            feature,
            payload,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
            instruction=instruction,
        )
        return JSONResponse(status_code=_status_for_submit(response), content=response)

    @app.get("/api/task/{task_id}")
    async def get_api_task(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("task_query", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=_status_for_query(guard), content=guard)
        task_guard = _task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if task_guard is not None:
            return JSONResponse(status_code=_status_for_query(task_guard), content=task_guard)
        response = get_result(task_id)
        return JSONResponse(status_code=_status_for_query(response), content=response)

    @app.get("/api/task/{task_id}/events")
    async def get_api_task_events(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("task_events", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=_status_for_query(guard), content=guard)
        task_guard = _task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if task_guard is not None:
            return JSONResponse(status_code=_status_for_query(task_guard), content=task_guard)
        response = stream_events(task_id)
        return JSONResponse(status_code=_status_for_query(response), content=response)

    @app.get("/api/task/{task_id}/compliance")
    async def get_api_task_compliance(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("task_compliance", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=_status_for_query(guard), content=guard)
        task_guard = _task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if task_guard is not None:
            return JSONResponse(status_code=_status_for_query(task_guard), content=task_guard)
        response = get_compliance_feedback(task_id)
        return JSONResponse(status_code=_status_for_query(response), content=response)

    @app.get("/api/history")
    async def get_api_history(
        limit: int = Query(default=50, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        command: Optional[str] = Query(default=None),
        tenant_id: Optional[str] = Query(default=None),
        operator_id: Optional[str] = Query(default=None),
        status: Optional[str] = Query(default=None),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
    ):
        guard = _access_guard("history_list", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=_status_for_generic(guard), content=guard)
        response = list_history(
            limit=limit,
            offset=offset,
            command=command,
            tenant_id=tenant_id,
            operator_id=operator_id,
            status=status,
        )
        return JSONResponse(status_code=_status_for_generic(response), content=response)

    @app.delete("/api/history/{task_id}")
    async def delete_api_history(
        task_id: str,
        purge_events: bool = Query(default=True),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
    ):
        guard = _access_guard("history_delete", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=_status_for_generic(guard), content=guard)
        response = delete_history(task_id, purge_events=purge_events)
        return JSONResponse(status_code=_status_for_generic(response), content=response)

    @app.get("/api/logs")
    async def get_api_logs(
        task_id: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=2000),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
    ):
        guard = _access_guard("logs_list", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=_status_for_generic(guard), content=guard)
        response = list_logs(task_id=task_id, limit=limit)
        return JSONResponse(status_code=_status_for_generic(response), content=response)

    @app.post("/api/logs/archive")
    async def post_api_logs_archive(
        force: bool = Query(default=False),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
    ):
        guard = _access_guard("logs_archive", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=_status_for_generic(guard), content=guard)
        response = archive_logs(force=force)
        return JSONResponse(status_code=_status_for_generic(response), content=response)

    @app.get("/api/runtime/queue")
    async def get_api_runtime_queue(api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header)):
        guard = _access_guard("runtime_queue", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=_status_for_generic(guard), content=guard)
        response = queue_runtime()
        return JSONResponse(status_code=_status_for_generic(response), content=response)

    @app.get("/api/runtime/exposure")
    async def get_api_runtime_exposure(api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header)):
        guard = _access_guard("runtime_exposure", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=_status_for_generic(guard), content=guard)
        response = {
            "status": "ok",
            "mapping": HTTP_ACCESS.command_by_feature(),
            "config": {
                "http": HTTP_ACCESS.redacted(),
                "sdk": SDK_ACCESS.redacted(),
            },
        }
        return JSONResponse(status_code=200, content=response)

    @app.get("/api/{feature}/{task_id}")
    async def get_api_feature_task(
        feature: str,
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("feature_query", api_key=api_key, feature=feature, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=_status_for_query(guard), content=guard)
        task_guard = _task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if task_guard is not None:
            return JSONResponse(status_code=_status_for_query(task_guard), content=task_guard)
        response, status_code = _check_task_feature_match(feature, task_id)
        return JSONResponse(status_code=status_code, content=response)

    @app.get("/api/{feature}/{task_id}/events")
    async def get_api_feature_task_events(
        feature: str,
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("feature_events", api_key=api_key, feature=feature, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=_status_for_query(guard), content=guard)
        task_guard = _task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if task_guard is not None:
            return JSONResponse(status_code=_status_for_query(task_guard), content=task_guard)
        check, status_code = _check_task_feature_match(feature, task_id)
        if status_code != 200:
            return JSONResponse(status_code=status_code, content=check)
        response = stream_events(task_id)
        return JSONResponse(status_code=_status_for_query(response), content=response)

    @app.get("/api/{feature}/{task_id}/compliance")
    async def get_api_feature_task_compliance(
        feature: str,
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("feature_compliance", api_key=api_key, feature=feature, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=_status_for_query(guard), content=guard)
        task_guard = _task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if task_guard is not None:
            return JSONResponse(status_code=_status_for_query(task_guard), content=task_guard)
        check, status_code = _check_task_feature_match(feature, task_id)
        if status_code != 200:
            return JSONResponse(status_code=status_code, content=check)
        response = get_compliance_feedback(task_id)
        return JSONResponse(status_code=_status_for_query(response), content=response)

    # Legacy endpoints kept for compatibility but disabled by default.
    @app.post("/task")
    async def post_task(
        payload: Dict[str, Any] = Body(...),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
    ):
        guard = _access_guard("legacy_task_submit", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=_status_for_submit(guard), content=guard)
        response = submit_task(payload, owner_api_key=api_key)
        return JSONResponse(status_code=_status_for_submit(response), content=response)

    @app.get("/task/{task_id}")
    async def get_task(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("legacy_task_query", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=_status_for_query(guard), content=guard)
        task_guard = _task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if task_guard is not None:
            return JSONResponse(status_code=_status_for_query(task_guard), content=task_guard)
        response = get_result(task_id)
        return JSONResponse(status_code=_status_for_query(response), content=response)

    @app.get("/task/{task_id}/events")
    async def get_task_events(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("legacy_task_events", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=_status_for_query(guard), content=guard)
        task_guard = _task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if task_guard is not None:
            return JSONResponse(status_code=_status_for_query(task_guard), content=task_guard)
        response = stream_events(task_id)
        return JSONResponse(status_code=_status_for_query(response), content=response)

    @app.get("/task/{task_id}/compliance")
    async def get_task_compliance(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = _access_guard("legacy_task_compliance", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=_status_for_query(guard), content=guard)
        task_guard = _task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if task_guard is not None:
            return JSONResponse(status_code=_status_for_query(task_guard), content=task_guard)
        response = get_compliance_feedback(task_id)
        return JSONResponse(status_code=_status_for_query(response), content=response)

    return app


try:
    app = create_app()
except RuntimeError:  # pragma: no cover
    app = None


if __name__ == "__main__":  # pragma: no cover
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("Run server requires `uvicorn` to be installed.") from exc

    uvicorn.run(create_app(), host="0.0.0.0", port=8000, reload=False)
