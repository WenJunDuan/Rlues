"""Schema validator utility with layered error codes."""

from __future__ import annotations

from typing import Any, Dict, List


SCHEMA_OK = "OK"
SCHEMA_MISSING_FIELD = "SCHEMA_MISSING_FIELD"
SCHEMA_TYPE_MISMATCH = "SCHEMA_TYPE_MISMATCH"
SCHEMA_INVALID_VALUE = "SCHEMA_INVALID_VALUE"


_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return _is_int(value) or isinstance(value, float)


def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _response(ok: bool, code: str, message: str, errors: List[dict], meta: Dict[str, Any] | None = None) -> dict:
    return {
        "ok": ok,
        "code": code,
        "message": message,
        "data": {"valid": ok, "errors": errors},
        "meta": {"plugin": "schema_validator", **(meta or {})},
    }


def validate(data: dict, schema: dict) -> dict:
    errors: List[dict] = []

    if not isinstance(data, dict):
        return _response(False, SCHEMA_TYPE_MISMATCH, "data must be object", [{"path": "$", "actual": type(data).__name__}], {"input_size": 0})

    if not isinstance(schema, dict):
        return _response(False, SCHEMA_TYPE_MISMATCH, "schema must be object", [{"path": "schema", "actual": type(schema).__name__}], {"input_size": len(data)})

    required = schema.get("required", [])
    if isinstance(required, list):
        for field in required:
            if field not in data:
                errors.append({"path": field, "reason": "missing"})
    if errors:
        return _response(False, SCHEMA_MISSING_FIELD, "required fields missing", errors, {"input_size": len(data)})

    props = schema.get("properties", {})
    if isinstance(props, dict):
        for key, rule in props.items():
            if key not in data:
                continue
            value = data[key]
            if isinstance(rule, dict) and rule.get("nullable") and value is None:
                continue
            expected_type = rule.get("type") if isinstance(rule, dict) else None
            if expected_type in _TYPE_MAP and not isinstance(value, _TYPE_MAP[expected_type]):
                errors.append({"path": key, "expected": expected_type, "actual": type(value).__name__})

            if isinstance(rule, dict) and "enum" in rule and value not in rule["enum"]:
                errors.append({"path": key, "reason": "invalid_enum", "value": value, "allowed": rule["enum"]})

    if errors:
        code = SCHEMA_TYPE_MISMATCH if any("expected" in e for e in errors) else SCHEMA_INVALID_VALUE
        return _response(False, code, "schema validation failed", errors, {"input_size": len(data)})

    return _response(True, SCHEMA_OK, "schema validation passed", [], {"input_size": len(data)})


def validate_task_envelope(data: dict) -> dict:
    schema = {
        "required": ["task_id", "command", "context", "payload"],
        "properties": {
            "task_id": {"type": "string"},
            "command": {"type": "string"},
            "context": {"type": "object"},
            "payload": {"type": "object"},
            "runtime": {"type": "object"},
        },
    }
    result = validate(data, schema)
    if not result["ok"]:
        return result

    context = data.get("context", {})
    missing = []
    for key in ["tenant_id", "operator_id"]:
        if key not in context:
            missing.append({"path": f"context.{key}", "reason": "missing"})
    if missing:
        return _response(False, SCHEMA_MISSING_FIELD, "context required fields missing", missing, {"input_size": len(data)})
    for key in ["tenant_id", "operator_id"]:
        value = context.get(key)
        if not isinstance(value, str):
            return _response(
                False,
                SCHEMA_TYPE_MISMATCH,
                f"context.{key} must be string",
                [{"path": f"context.{key}", "expected": "string", "actual": type(value).__name__}],
                {"input_size": len(data)},
            )
        if not value.strip():
            return _response(
                False,
                SCHEMA_INVALID_VALUE,
                f"context.{key} must be non-empty",
                [{"path": f"context.{key}", "value": value}],
                {"input_size": len(data)},
            )

    command = data.get("command")
    if not isinstance(command, str):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "command must be string",
            [{"path": "command", "expected": "string", "actual": type(command).__name__}],
            {"input_size": len(data)},
        )
    if not command.startswith("/"):
        return _response(
            False,
            SCHEMA_INVALID_VALUE,
            "command must start with '/'",
            [{"path": "command", "value": command}],
            {"input_size": len(data)},
        )

    payload = data.get("payload")
    if not isinstance(payload, dict):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "payload must be object",
            [{"path": "payload", "expected": "object", "actual": type(payload).__name__}],
            {"input_size": len(data)},
        )

    runtime = data.get("runtime")
    if runtime is not None and not isinstance(runtime, dict):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "runtime must be object when provided",
            [{"path": "runtime", "expected": "object", "actual": type(runtime).__name__}],
            {"input_size": len(data)},
        )

    return result


def validate_result_envelope(data: dict) -> dict:
    schema = {
        "required": ["task_id", "command", "status", "result", "execution", "error"],
        "properties": {
            "task_id": {"type": "string"},
            "command": {"type": "string"},
            "status": {"type": "string", "enum": ["completed", "needs_review", "failed", "timeout"]},
            "result": {"type": "object"},
            "execution": {"type": "object"},
            "error": {"type": "object", "nullable": True},
        },
    }
    result = validate(data, schema)
    if not result["ok"]:
        return result

    result_data = data.get("result", {})
    execution_data = data.get("execution", {})
    error_data = data.get("error")

    result_required = ["decision", "confidence", "summary", "issues", "evidence"]
    missing = [{"path": f"result.{field}", "reason": "missing"} for field in result_required if field not in result_data]
    if missing:
        return _response(False, SCHEMA_MISSING_FIELD, "result required fields missing", missing, {"input_size": len(data)})

    decision = result_data.get("decision")
    allowed = ["approved", "rejected", "needs_review"]
    if decision not in allowed:
        return _response(
            False,
            SCHEMA_INVALID_VALUE,
            "result.decision invalid",
            [{"path": "result.decision", "value": decision, "allowed": allowed}],
            {"input_size": len(data)},
        )

    confidence = result_data.get("confidence")
    if not _is_number(confidence):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "result.confidence must be number",
            [{"path": "result.confidence", "expected": "number", "actual": type(confidence).__name__}],
            {"input_size": len(data)},
        )
    confidence = float(confidence)
    if confidence < 0.0 or confidence > 1.0:
        return _response(
            False,
            SCHEMA_INVALID_VALUE,
            "result.confidence out of range",
            [{"path": "result.confidence", "value": confidence}],
            {"input_size": len(data)},
        )

    if not isinstance(result_data.get("summary"), str):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "result.summary must be string",
            [{"path": "result.summary", "expected": "string", "actual": type(result_data.get("summary")).__name__}],
            {"input_size": len(data)},
        )

    issues = result_data.get("issues")
    if not isinstance(issues, list):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "result.issues must be array",
            [{"path": "result.issues", "expected": "array", "actual": type(issues).__name__}],
            {"input_size": len(data)},
        )

    severity_allowed = ["error", "warning", "info"]
    for idx, issue in enumerate(issues):
        base = f"result.issues[{idx}]"
        if not isinstance(issue, dict):
            return _response(
                False,
                SCHEMA_TYPE_MISMATCH,
                f"{base} must be object",
                [{"path": base, "expected": "object", "actual": type(issue).__name__}],
                {"input_size": len(data)},
            )

        missing_issue = [{"path": f"{base}.{field}", "reason": "missing"} for field in ["severity", "category", "description"] if field not in issue]
        if missing_issue:
            return _response(False, SCHEMA_MISSING_FIELD, f"{base} required fields missing", missing_issue, {"input_size": len(data)})

        if issue.get("severity") not in severity_allowed:
            return _response(
                False,
                SCHEMA_INVALID_VALUE,
                f"{base}.severity invalid",
                [{"path": f"{base}.severity", "value": issue.get("severity"), "allowed": severity_allowed}],
                {"input_size": len(data)},
            )

        for field in ["category", "description"]:
            if not isinstance(issue.get(field), str):
                return _response(
                    False,
                    SCHEMA_TYPE_MISMATCH,
                    f"{base}.{field} must be string",
                    [{"path": f"{base}.{field}", "expected": "string", "actual": type(issue.get(field)).__name__}],
                    {"input_size": len(data)},
                )
        if "evidence_ref" in issue and issue["evidence_ref"] is not None and not isinstance(issue["evidence_ref"], str):
            return _response(
                False,
                SCHEMA_TYPE_MISMATCH,
                f"{base}.evidence_ref must be string",
                [{"path": f"{base}.evidence_ref", "expected": "string", "actual": type(issue["evidence_ref"]).__name__}],
                {"input_size": len(data)},
            )

    evidence = result_data.get("evidence")
    if not isinstance(evidence, list):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "result.evidence must be array",
            [{"path": "result.evidence", "expected": "array", "actual": type(evidence).__name__}],
            {"input_size": len(data)},
        )

    for idx, item in enumerate(evidence):
        base = f"result.evidence[{idx}]"
        if not isinstance(item, dict):
            return _response(
                False,
                SCHEMA_TYPE_MISMATCH,
                f"{base} must be object",
                [{"path": base, "expected": "object", "actual": type(item).__name__}],
                {"input_size": len(data)},
            )
        missing_ev = [{"path": f"{base}.{field}", "reason": "missing"} for field in ["id", "type", "source", "content"] if field not in item]
        if missing_ev:
            return _response(False, SCHEMA_MISSING_FIELD, f"{base} required fields missing", missing_ev, {"input_size": len(data)})

        for field in ["id", "type", "source", "content"]:
            if not isinstance(item.get(field), str):
                return _response(
                    False,
                    SCHEMA_TYPE_MISMATCH,
                    f"{base}.{field} must be string",
                    [{"path": f"{base}.{field}", "expected": "string", "actual": type(item.get(field)).__name__}],
                    {"input_size": len(data)},
                )

    execution_required = ["model_used", "agents_invoked", "parallel_tasks", "tools_called"]
    missing_exec = [{"path": f"execution.{field}", "reason": "missing"} for field in execution_required if field not in execution_data]
    if missing_exec:
        return _response(False, SCHEMA_MISSING_FIELD, "execution required fields missing", missing_exec, {"input_size": len(data)})

    if not isinstance(execution_data.get("model_used"), str):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "execution.model_used must be string",
            [{"path": "execution.model_used", "expected": "string", "actual": type(execution_data.get("model_used")).__name__}],
            {"input_size": len(data)},
        )

    agents_invoked = execution_data.get("agents_invoked")
    if not isinstance(agents_invoked, list) or any(not isinstance(item, str) for item in agents_invoked):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "execution.agents_invoked must be array[string]",
            [{"path": "execution.agents_invoked", "expected": "array[string]"}],
            {"input_size": len(data)},
        )

    parallel_tasks = execution_data.get("parallel_tasks")
    if not _is_int(parallel_tasks):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "execution.parallel_tasks must be integer",
            [{"path": "execution.parallel_tasks", "expected": "integer", "actual": type(parallel_tasks).__name__}],
            {"input_size": len(data)},
        )
    if parallel_tasks < 0:
        return _response(
            False,
            SCHEMA_INVALID_VALUE,
            "execution.parallel_tasks must be >= 0",
            [{"path": "execution.parallel_tasks", "value": parallel_tasks}],
            {"input_size": len(data)},
        )

    tools_called = execution_data.get("tools_called")
    if not isinstance(tools_called, list) or any(not isinstance(item, str) for item in tools_called):
        return _response(
            False,
            SCHEMA_TYPE_MISMATCH,
            "execution.tools_called must be array[string]",
            [{"path": "execution.tools_called", "expected": "array[string]"}],
            {"input_size": len(data)},
        )

    if error_data is not None:
        if not isinstance(error_data, dict):
            return _response(
                False,
                SCHEMA_TYPE_MISMATCH,
                "error must be object or null",
                [{"path": "error", "expected": "object|null", "actual": type(error_data).__name__}],
                {"input_size": len(data)},
            )
        missing_error = [{"path": f"error.{field}", "reason": "missing"} for field in ["code", "message", "recoverable"] if field not in error_data]
        if missing_error:
            return _response(False, SCHEMA_MISSING_FIELD, "error required fields missing", missing_error, {"input_size": len(data)})
        if not isinstance(error_data.get("code"), str):
            return _response(
                False,
                SCHEMA_TYPE_MISMATCH,
                "error.code must be string",
                [{"path": "error.code", "expected": "string", "actual": type(error_data.get("code")).__name__}],
                {"input_size": len(data)},
            )
        if not isinstance(error_data.get("message"), str):
            return _response(
                False,
                SCHEMA_TYPE_MISMATCH,
                "error.message must be string",
                [{"path": "error.message", "expected": "string", "actual": type(error_data.get("message")).__name__}],
                {"input_size": len(data)},
            )
        if not isinstance(error_data.get("recoverable"), bool):
            return _response(
                False,
                SCHEMA_TYPE_MISMATCH,
                "error.recoverable must be boolean",
                [{"path": "error.recoverable", "expected": "boolean", "actual": type(error_data.get("recoverable")).__name__}],
                {"input_size": len(data)},
            )
        if "details" in error_data and error_data["details"] is not None and not isinstance(error_data["details"], list):
            return _response(
                False,
                SCHEMA_TYPE_MISMATCH,
                "error.details must be array",
                [{"path": "error.details", "expected": "array", "actual": type(error_data["details"]).__name__}],
                {"input_size": len(data)},
            )

    if data.get("status") == "failed" and error_data is None:
        return _response(
            False,
            SCHEMA_INVALID_VALUE,
            "failed status requires error payload",
            [{"path": "error", "reason": "required_when_status_failed"}],
            {"input_size": len(data)},
        )

    return result
