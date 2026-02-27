"""Schema validators for adapter input/output envelopes."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .error_codes import (
    VALIDATION_INVALID_VALUE,
    VALIDATION_MISSING_FIELD,
    VALIDATION_TYPE_MISMATCH,
)


ValidationResult = Dict[str, Any]
_COMMANDS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "commands"
_DEFAULT_ALLOWED_COMMANDS = frozenset({"/audit"})

# TTL-based cache for allowed commands (E6 fix: replaces @lru_cache)
_commands_cache: frozenset[str] | None = None
_commands_cache_ts: float = 0.0
_COMMANDS_CACHE_TTL = 60.0  # seconds


def _ok() -> ValidationResult:
    return {"ok": True, "code": "OK", "message": "valid", "details": []}


def _fail(code: str, message: str, details: List[dict]) -> ValidationResult:
    return {"ok": False, "code": code, "message": message, "details": details}


def _type_name(value: Any) -> str:
    return type(value).__name__


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return (isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)


def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_invoice_date(value: str) -> bool:
    try:
        datetime.strptime(value.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _parse_timepoint(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None

    # Accept either date-only or ISO-like datetime text.
    if len(text) == 10:
        try:
            return datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return None

    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _scan_commands_dir() -> frozenset[str]:
    """Scan .claude/commands/*.md and return allowed command names."""
    if not _COMMANDS_DIR.exists():
        return _DEFAULT_ALLOWED_COMMANDS

    commands: set[str] = set()
    for path in sorted(_COMMANDS_DIR.glob("*.md")):
        stem = path.stem.strip()
        if not stem:
            continue
        commands.add(f"/{stem}")
    return frozenset(commands or _DEFAULT_ALLOWED_COMMANDS)


def _load_allowed_commands() -> frozenset[str]:
    """Load allowed commands with a TTL-based cache (60s)."""
    global _commands_cache, _commands_cache_ts
    now = time.monotonic()
    if _commands_cache is not None and (now - _commands_cache_ts) < _COMMANDS_CACHE_TTL:
        return _commands_cache
    _commands_cache = _scan_commands_dir()
    _commands_cache_ts = now
    return _commands_cache


def _validate_audit_payload(payload: Dict[str, Any]) -> ValidationResult:
    report = payload.get("expense_report")
    if report is None:
        return _fail(
            VALIDATION_MISSING_FIELD,
            "payload.expense_report is required for /audit",
            [{"path": "payload.expense_report", "reason": "missing"}],
        )
    if not isinstance(report, dict):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "payload.expense_report must be object",
            [{"path": "payload.expense_report", "expected": "object", "actual": _type_name(report)}],
        )

    report_required_str = ["report_id", "employee_id", "reason", "currency", "department", "level"]
    for field in report_required_str:
        if field not in report:
            return _fail(
                VALIDATION_MISSING_FIELD,
                f"payload.expense_report.{field} is required for /audit",
                [{"path": f"payload.expense_report.{field}", "reason": "missing"}],
            )
        if not _is_non_empty_str(report.get(field)):
            return _fail(
                VALIDATION_INVALID_VALUE,
                f"payload.expense_report.{field} must be non-empty string",
                [{"path": f"payload.expense_report.{field}", "value": report.get(field)}],
            )

    total_amount = report.get("total_amount")
    if total_amount is None:
        return _fail(
            VALIDATION_MISSING_FIELD,
            "payload.expense_report.total_amount is required for /audit",
            [{"path": "payload.expense_report.total_amount", "reason": "missing"}],
        )
    if not _is_number(total_amount):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "payload.expense_report.total_amount must be number",
            [{"path": "payload.expense_report.total_amount", "expected": "number", "actual": _type_name(total_amount)}],
        )
    if float(total_amount) <= 0:
        return _fail(
            VALIDATION_INVALID_VALUE,
            "payload.expense_report.total_amount must be > 0",
            [{"path": "payload.expense_report.total_amount", "value": total_amount}],
        )

    invoices = report.get("invoices")
    if invoices is None:
        return _fail(
            VALIDATION_MISSING_FIELD,
            "payload.expense_report.invoices is required for /audit",
            [{"path": "payload.expense_report.invoices", "reason": "missing"}],
        )
    if not isinstance(invoices, list):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "payload.expense_report.invoices must be array",
            [{"path": "payload.expense_report.invoices", "expected": "array", "actual": _type_name(invoices)}],
        )
    if not invoices:
        return _fail(
            VALIDATION_INVALID_VALUE,
            "payload.expense_report.invoices must be non-empty",
            [{"path": "payload.expense_report.invoices", "reason": "empty"}],
        )

    invoice_required_str = ["invoice_code", "invoice_number", "date", "category", "currency"]
    for idx, invoice in enumerate(invoices):
        base = f"payload.expense_report.invoices[{idx}]"
        if not isinstance(invoice, dict):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                f"{base} must be object",
                [{"path": base, "expected": "object", "actual": _type_name(invoice)}],
            )
        for field in invoice_required_str:
            if field not in invoice:
                return _fail(
                    VALIDATION_MISSING_FIELD,
                    f"{base}.{field} is required for /audit",
                    [{"path": f"{base}.{field}", "reason": "missing"}],
                )
            if not _is_non_empty_str(invoice.get(field)):
                return _fail(
                    VALIDATION_INVALID_VALUE,
                    f"{base}.{field} must be non-empty string",
                    [{"path": f"{base}.{field}", "value": invoice.get(field)}],
                )
        invoice_date = str(invoice.get("date", "")).strip()
        if not _parse_invoice_date(invoice_date):
            return _fail(
                VALIDATION_INVALID_VALUE,
                f"{base}.date must be YYYY-MM-DD",
                [{"path": f"{base}.date", "value": invoice.get("date")}],
            )
        amount = invoice.get("amount")
        if not _is_number(amount):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                f"{base}.amount must be number",
                [{"path": f"{base}.amount", "expected": "number", "actual": _type_name(amount)}],
            )
        if float(amount) <= 0:
            return _fail(
                VALIDATION_INVALID_VALUE,
                f"{base}.amount must be > 0",
                [{"path": f"{base}.amount", "value": amount}],
            )

    applicant = payload.get("applicant")
    if applicant is None:
        return _fail(
            VALIDATION_MISSING_FIELD,
            "payload.applicant is required for /audit",
            [{"path": "payload.applicant", "reason": "missing"}],
        )
    if not isinstance(applicant, dict):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "payload.applicant must be object",
            [{"path": "payload.applicant", "expected": "object", "actual": _type_name(applicant)}],
        )
    for field in ["employee_id", "name", "position"]:
        if not _is_non_empty_str(applicant.get(field)):
            return _fail(
                VALIDATION_INVALID_VALUE,
                f"payload.applicant.{field} must be non-empty string",
                [{"path": f"payload.applicant.{field}", "value": applicant.get(field)}],
            )

    has_trip = "trip_application" in payload
    has_outing = "outing_application" in payload
    if not has_trip and not has_outing:
        return _fail(
            VALIDATION_MISSING_FIELD,
            "payload.trip_application or payload.outing_application is required for /audit",
            [{"path": "payload.trip_application|payload.outing_application", "reason": "missing"}],
        )
    for key in ["trip_application", "outing_application"]:
        if key not in payload:
            continue
        req = payload.get(key)
        if not isinstance(req, dict):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                f"payload.{key} must be object",
                [{"path": f"payload.{key}", "expected": "object", "actual": _type_name(req)}],
            )
        for field in ["request_id", "reason", "start_at", "end_at"]:
            if not _is_non_empty_str(req.get(field)):
                return _fail(
                    VALIDATION_INVALID_VALUE,
                    f"payload.{key}.{field} must be non-empty string",
                    [{"path": f"payload.{key}.{field}", "value": req.get(field)}],
                )
        start_text = str(req.get("start_at", "")).strip()
        end_text = str(req.get("end_at", "")).strip()
        start_at = _parse_timepoint(start_text)
        end_at = _parse_timepoint(end_text)
        if start_at is None:
            return _fail(
                VALIDATION_INVALID_VALUE,
                f"payload.{key}.start_at must be date or ISO datetime",
                [{"path": f"payload.{key}.start_at", "value": req.get("start_at")}],
            )
        if end_at is None:
            return _fail(
                VALIDATION_INVALID_VALUE,
                f"payload.{key}.end_at must be date or ISO datetime",
                [{"path": f"payload.{key}.end_at", "value": req.get("end_at")}],
            )
        if end_at < start_at:
            return _fail(
                VALIDATION_INVALID_VALUE,
                f"payload.{key}.end_at must be >= start_at",
                [
                    {"path": f"payload.{key}.start_at", "value": req.get("start_at")},
                    {"path": f"payload.{key}.end_at", "value": req.get("end_at")},
                ],
            )

    policy_pack = payload.get("policy_pack")
    if policy_pack is None:
        return _fail(
            VALIDATION_MISSING_FIELD,
            "payload.policy_pack is required for /audit",
            [{"path": "payload.policy_pack", "reason": "missing"}],
        )
    if not isinstance(policy_pack, dict):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "payload.policy_pack must be object",
            [{"path": "payload.policy_pack", "expected": "object", "actual": _type_name(policy_pack)}],
        )
    if not _is_non_empty_str(policy_pack.get("policy_id")):
        return _fail(
            VALIDATION_INVALID_VALUE,
            "payload.policy_pack.policy_id must be non-empty string",
            [{"path": "payload.policy_pack.policy_id", "value": policy_pack.get("policy_id")}],
        )
    if not _is_non_empty_str(policy_pack.get("policy_version")):
        return _fail(
            VALIDATION_INVALID_VALUE,
            "payload.policy_pack.policy_version must be non-empty string",
            [{"path": "payload.policy_pack.policy_version", "value": policy_pack.get("policy_version")}],
        )
    rules = policy_pack.get("rules")
    if not isinstance(rules, list) or not rules:
        return _fail(
            VALIDATION_INVALID_VALUE,
            "payload.policy_pack.rules must be non-empty array",
            [{"path": "payload.policy_pack.rules", "value": rules}],
        )
    if any(not isinstance(rule, str) or not rule.strip() for rule in rules):
        return _fail(
            VALIDATION_INVALID_VALUE,
            "payload.policy_pack.rules must be array of non-empty strings",
            [{"path": "payload.policy_pack.rules", "value": rules}],
        )

    return _ok()


def _validate_command_payload(command: str, payload: Dict[str, Any]) -> ValidationResult:
    allowed_commands = _load_allowed_commands()
    if command not in allowed_commands:
        return _fail(
            VALIDATION_INVALID_VALUE,
            "unsupported command",
            [{"path": "command", "value": command, "allowed": sorted(allowed_commands)}],
        )

    if command == "/audit":
        return _validate_audit_payload(payload)
    return _ok()


def validate_task_envelope(payload: Dict[str, Any]) -> ValidationResult:
    details: List[dict] = []

    if not isinstance(payload, dict):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "payload must be an object",
            [{"path": "$", "expected": "object", "actual": _type_name(payload)}],
        )

    required_root = ["task_id", "command", "context", "payload"]
    for key in required_root:
        if key not in payload:
            details.append({"path": key, "reason": "missing"})
    if details:
        return _fail(VALIDATION_MISSING_FIELD, "required fields missing", details)

    # task_id
    task_id = payload.get("task_id")
    if not isinstance(task_id, str):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "task_id must be string",
            [{"path": "task_id", "expected": "string", "actual": _type_name(task_id)}],
        )
    if not task_id.strip():
        return _fail(
            VALIDATION_INVALID_VALUE,
            "task_id must be non-empty",
            [{"path": "task_id", "reason": "empty"}],
        )

    # command
    command = payload.get("command")
    if not isinstance(command, str):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "command must be string",
            [{"path": "command", "expected": "string", "actual": _type_name(command)}],
        )
    if not command.startswith("/"):
        return _fail(
            VALIDATION_INVALID_VALUE,
            "command must start with '/'",
            [{"path": "command", "value": command}],
        )

    # context
    context = payload.get("context")
    if not isinstance(context, dict):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "context must be object",
            [{"path": "context", "expected": "object", "actual": _type_name(context)}],
        )

    for key in ["tenant_id", "operator_id"]:
        if key not in context:
            details.append({"path": f"context.{key}", "reason": "missing"})
    if details:
        return _fail(VALIDATION_MISSING_FIELD, "required context fields missing", details)

    for key in ["tenant_id", "operator_id"]:
        value = context.get(key)
        if not isinstance(value, str):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                f"context.{key} must be string",
                [{"path": f"context.{key}", "expected": "string", "actual": _type_name(value)}],
            )
        if not value.strip():
            return _fail(
                VALIDATION_INVALID_VALUE,
                f"context.{key} must be non-empty",
                [{"path": f"context.{key}", "reason": "empty"}],
            )

    # payload
    biz_payload = payload.get("payload")
    if not isinstance(biz_payload, dict):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "payload must be object",
            [{"path": "payload", "expected": "object", "actual": _type_name(biz_payload)}],
        )

    command_payload_validation = _validate_command_payload(command, biz_payload)
    if not command_payload_validation["ok"]:
        return command_payload_validation

    # runtime (optional)
    runtime = payload.get("runtime")
    if runtime is not None:
        if not isinstance(runtime, dict):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                "runtime must be object",
                [{"path": "runtime", "expected": "object", "actual": _type_name(runtime)}],
            )

        int_fields = ["max_tokens", "timeout_sec"]
        for field in int_fields:
            if field in runtime:
                value = runtime[field]
                if not _is_int(value):
                    return _fail(
                        VALIDATION_TYPE_MISMATCH,
                        f"runtime.{field} must be integer",
                        [{"path": f"runtime.{field}", "expected": "integer", "actual": _type_name(value)}],
                    )
                if value <= 0:
                    return _fail(
                        VALIDATION_INVALID_VALUE,
                        f"runtime.{field} must be > 0",
                        [{"path": f"runtime.{field}", "value": value}],
                    )

        str_fields = ["model", "trace_id", "rules_version"]
        for field in str_fields:
            if field in runtime and runtime[field] is not None and not isinstance(runtime[field], str):
                return _fail(
                    VALIDATION_TYPE_MISMATCH,
                    f"runtime.{field} must be string",
                    [{"path": f"runtime.{field}", "expected": "string", "actual": _type_name(runtime[field])}],
                )

    return _ok()


def validate_result_envelope(payload: Dict[str, Any]) -> ValidationResult:
    if not isinstance(payload, dict):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "result envelope must be object",
            [{"path": "$", "expected": "object", "actual": _type_name(payload)}],
        )

    required = ["task_id", "command", "status", "result", "execution", "error"]
    details = [{"path": k, "reason": "missing"} for k in required if k not in payload]
    if details:
        return _fail(VALIDATION_MISSING_FIELD, "required result fields missing", details)

    task_id = payload.get("task_id")
    if not isinstance(task_id, str):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "task_id must be string",
            [{"path": "task_id", "expected": "string", "actual": _type_name(task_id)}],
        )
    if not task_id.strip():
        return _fail(VALIDATION_INVALID_VALUE, "task_id must be non-empty", [{"path": "task_id", "reason": "empty"}])

    command = payload.get("command")
    if not isinstance(command, str):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "command must be string",
            [{"path": "command", "expected": "string", "actual": _type_name(command)}],
        )
    if not command.startswith("/"):
        return _fail(VALIDATION_INVALID_VALUE, "command must start with '/'", [{"path": "command", "value": command}])

    status = payload.get("status")
    allowed = {"completed", "needs_review", "failed", "timeout"}
    if status not in allowed:
        return _fail(
            VALIDATION_INVALID_VALUE,
            "invalid status",
            [{"path": "status", "value": status, "allowed": sorted(allowed)}],
        )

    result = payload.get("result")
    if not isinstance(result, dict):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "result must be object",
            [{"path": "result", "expected": "object", "actual": _type_name(result)}],
        )

    result_required = ["decision", "confidence", "summary", "issues", "evidence"]
    details = [{"path": f"result.{k}", "reason": "missing"} for k in result_required if k not in result]
    if details:
        return _fail(VALIDATION_MISSING_FIELD, "required result subfields missing", details)

    decision = result.get("decision")
    allowed_decisions = {"approved", "rejected", "needs_review"}
    if decision not in allowed_decisions:
        return _fail(
            VALIDATION_INVALID_VALUE,
            "invalid decision",
            [{"path": "result.decision", "value": decision, "allowed": sorted(allowed_decisions)}],
        )

    confidence = result.get("confidence")
    if not _is_number(confidence):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "result.confidence must be number",
            [{"path": "result.confidence", "expected": "number", "actual": _type_name(confidence)}],
        )
    confidence = float(confidence)
    if confidence < 0.0 or confidence > 1.0:
        return _fail(
            VALIDATION_INVALID_VALUE,
            "result.confidence must be between 0 and 1",
            [{"path": "result.confidence", "value": confidence}],
        )

    summary = result.get("summary")
    if not isinstance(summary, str):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "result.summary must be string",
            [{"path": "result.summary", "expected": "string", "actual": _type_name(summary)}],
        )

    issues = result.get("issues")
    if not isinstance(issues, list):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "result.issues must be array",
            [{"path": "result.issues", "expected": "array", "actual": _type_name(issues)}],
        )

    allowed_severity = {"error", "warning", "info"}
    for idx, issue in enumerate(issues):
        base = f"result.issues[{idx}]"
        if not isinstance(issue, dict):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                f"{base} must be object",
                [{"path": base, "expected": "object", "actual": _type_name(issue)}],
            )

        miss = [{"path": f"{base}.{k}", "reason": "missing"} for k in ("severity", "category", "description") if k not in issue]
        if miss:
            return _fail(VALIDATION_MISSING_FIELD, f"{base} required fields missing", miss)

        severity = issue.get("severity")
        if severity not in allowed_severity:
            return _fail(
                VALIDATION_INVALID_VALUE,
                f"{base}.severity invalid",
                [{"path": f"{base}.severity", "value": severity, "allowed": sorted(allowed_severity)}],
            )

        for key in ("category", "description"):
            value = issue.get(key)
            if not isinstance(value, str):
                return _fail(
                    VALIDATION_TYPE_MISMATCH,
                    f"{base}.{key} must be string",
                    [{"path": f"{base}.{key}", "expected": "string", "actual": _type_name(value)}],
                )

        if "evidence_ref" in issue and issue["evidence_ref"] is not None and not isinstance(issue["evidence_ref"], str):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                f"{base}.evidence_ref must be string",
                [{"path": f"{base}.evidence_ref", "expected": "string", "actual": _type_name(issue['evidence_ref'])}],
            )

    evidence = result.get("evidence")
    if not isinstance(evidence, list):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "result.evidence must be array",
            [{"path": "result.evidence", "expected": "array", "actual": _type_name(evidence)}],
        )

    for idx, item in enumerate(evidence):
        base = f"result.evidence[{idx}]"
        if not isinstance(item, dict):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                f"{base} must be object",
                [{"path": base, "expected": "object", "actual": _type_name(item)}],
            )

        miss = [{"path": f"{base}.{k}", "reason": "missing"} for k in ("id", "type", "source", "content") if k not in item]
        if miss:
            return _fail(VALIDATION_MISSING_FIELD, f"{base} required fields missing", miss)

        for key in ("id", "type", "source", "content"):
            value = item.get(key)
            if not isinstance(value, str):
                return _fail(
                    VALIDATION_TYPE_MISMATCH,
                    f"{base}.{key} must be string",
                    [{"path": f"{base}.{key}", "expected": "string", "actual": _type_name(value)}],
                )

    execution = payload.get("execution")
    if not isinstance(execution, dict):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "execution must be object",
            [{"path": "execution", "expected": "object", "actual": _type_name(execution)}],
        )

    execution_required = ["model_used", "agents_invoked", "parallel_tasks", "tools_called"]
    details = [{"path": f"execution.{k}", "reason": "missing"} for k in execution_required if k not in execution]
    if details:
        return _fail(VALIDATION_MISSING_FIELD, "required execution fields missing", details)

    model_used = execution.get("model_used")
    if not isinstance(model_used, str):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "execution.model_used must be string",
            [{"path": "execution.model_used", "expected": "string", "actual": _type_name(model_used)}],
        )

    agents_invoked = execution.get("agents_invoked")
    if not isinstance(agents_invoked, list):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "execution.agents_invoked must be array",
            [{"path": "execution.agents_invoked", "expected": "array", "actual": _type_name(agents_invoked)}],
        )
    for idx, agent in enumerate(agents_invoked):
        if not isinstance(agent, str):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                f"execution.agents_invoked[{idx}] must be string",
                [{"path": f"execution.agents_invoked[{idx}]", "expected": "string", "actual": _type_name(agent)}],
            )

    parallel_tasks = execution.get("parallel_tasks")
    if not _is_int(parallel_tasks):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "execution.parallel_tasks must be integer",
            [{"path": "execution.parallel_tasks", "expected": "integer", "actual": _type_name(parallel_tasks)}],
        )
    if parallel_tasks < 0:
        return _fail(
            VALIDATION_INVALID_VALUE,
            "execution.parallel_tasks must be >= 0",
            [{"path": "execution.parallel_tasks", "value": parallel_tasks}],
        )

    tools_called = execution.get("tools_called")
    if not isinstance(tools_called, list):
        return _fail(
            VALIDATION_TYPE_MISMATCH,
            "execution.tools_called must be array",
            [{"path": "execution.tools_called", "expected": "array", "actual": _type_name(tools_called)}],
        )
    for idx, tool in enumerate(tools_called):
        if not isinstance(tool, str):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                f"execution.tools_called[{idx}] must be string",
                [{"path": f"execution.tools_called[{idx}]", "expected": "string", "actual": _type_name(tool)}],
            )

    error = payload.get("error")
    if error is not None:
        if not isinstance(error, dict):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                "error must be object or null",
                [{"path": "error", "expected": "object|null", "actual": _type_name(error)}],
            )

        error_required = ["code", "message", "recoverable"]
        details = [{"path": f"error.{k}", "reason": "missing"} for k in error_required if k not in error]
        if details:
            return _fail(VALIDATION_MISSING_FIELD, "required error fields missing", details)

        if not isinstance(error.get("code"), str):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                "error.code must be string",
                [{"path": "error.code", "expected": "string", "actual": _type_name(error.get("code"))}],
            )
        if not isinstance(error.get("message"), str):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                "error.message must be string",
                [{"path": "error.message", "expected": "string", "actual": _type_name(error.get("message"))}],
            )
        if not isinstance(error.get("recoverable"), bool):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                "error.recoverable must be boolean",
                [{"path": "error.recoverable", "expected": "boolean", "actual": _type_name(error.get("recoverable"))}],
            )
        if "details" in error and error["details"] is not None and not isinstance(error["details"], list):
            return _fail(
                VALIDATION_TYPE_MISMATCH,
                "error.details must be array",
                [{"path": "error.details", "expected": "array", "actual": _type_name(error["details"])}],
            )

    if status == "failed" and error is None:
        return _fail(
            VALIDATION_INVALID_VALUE,
            "failed status requires error payload",
            [{"path": "error", "reason": "required_when_status_failed"}],
        )

    return _ok()
