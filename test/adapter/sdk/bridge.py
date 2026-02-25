"""SDK bridge for claude_agent_sdk integration.

This module provides a real SDK integration path and a safe fallback path.
It is not executed in this phase.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..core.error_codes import (
    SDK_EVENT_LOOP_ERROR,
    SDK_IMPORT_ERROR,
    SDK_OPTIONS_ERROR,
    SDK_QUERY_ERROR,
    SDK_RESULT_MAPPING_ERROR,
    error_payload,
)
from .access import SDK_ACCESS
from .runtime import load_claude_sdk_runtime
from ..core.types import ResultEnvelope, TaskEnvelope


@dataclass
class SdkExecutionResult:
    envelope: ResultEnvelope
    events: List[Dict[str, Any]]


COMMAND_AGENT_MAP = {
    "/audit": ["expense-auditor"],
}


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _agents_for_command(command: str) -> List[str]:
    return COMMAND_AGENT_MAP.get(command, ["orchestrator-fallback"])


def _sanitize_basis(value: Any, default: str = "insufficient evidence; manual review required") -> str:
    text = _safe_str(value, default=default)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        text = default
    return text[:180]


def _audit_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    snapshot = dict(payload)
    snapshot.setdefault("applicant", {})
    snapshot.setdefault("trip_application", {})
    snapshot.setdefault("outing_application", {})
    snapshot.setdefault("expense_report", {})
    snapshot.setdefault("policy_pack", {})
    snapshot.setdefault("invoice_verify", None)
    snapshot.setdefault("additional_documents", {})
    return snapshot


def _has_issue_category(issues: List[Dict[str, Any]], category: str) -> bool:
    target = category.strip().lower()
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        if _safe_str(issue.get("category"), "").lower() == target:
            return True
    return False


def _ensure_proxy_reimbursement_warning(result: Dict[str, Any], payload: Optional[Dict[str, Any]]) -> None:
    if not isinstance(payload, dict):
        return
    applicant = payload.get("applicant")
    expense_report = payload.get("expense_report")
    if not isinstance(applicant, dict) or not isinstance(expense_report, dict):
        return

    applicant_id = _safe_str(applicant.get("employee_id"))
    report_id = _safe_str(expense_report.get("employee_id"))
    if not applicant_id or not report_id or applicant_id == report_id:
        return

    issues = result.get("issues")
    if not isinstance(issues, list):
        issues = []
        result["issues"] = issues
    if _has_issue_category(issues, "proxy_reimbursement"):
        return

    issues.append(
        {
            "severity": "warning",
            "category": "proxy_reimbursement",
            "description": "applicant and reimbursement employee differ; suspected proxy reimbursement",
            "evidence_ref": "proxy-check-001",
        }
    )

    evidence = result.get("evidence")
    if not isinstance(evidence, list):
        evidence = []
        result["evidence"] = evidence
    evidence.append(
        {
            "id": "proxy-check-001",
            "type": "consistency",
            "source": "rule://proxy-reimbursement",
            "content": f"applicant.employee_id={applicant_id}, expense_report.employee_id={report_id}",
        }
    )

    downgraded_for_proxy = False
    if result.get("decision") == "approved":
        result["decision"] = "needs_review"
        downgraded_for_proxy = True
    if isinstance(result.get("confidence"), (int, float)) and float(result["confidence"]) > 0.69:
        result["confidence"] = 0.69
    proxy_warning_summary = "suspected proxy reimbursement; manual review recommended"
    current_summary = _safe_str(result.get("summary"))
    if not current_summary:
        result["summary"] = proxy_warning_summary
    elif downgraded_for_proxy and "proxy reimbursement" not in current_summary.lower():
        result["summary"] = _sanitize_basis(f"{current_summary}; {proxy_warning_summary}")


def _build_audit_prompt(task: TaskEnvelope) -> str:
    snapshot = _audit_snapshot(task.payload)
    serialized = json.dumps(snapshot, ensure_ascii=False, indent=2)
    return (
        "You are an enterprise reimbursement compliance reviewer.\n"
        "Assess whether this reimbursement is compliant based on provided policy and documents.\n"
        "This is the first-gate screening system.\n"
        "Do not expose thought process, chain-of-thought, or calculation details.\n"
        "Return EXACTLY one JSON object with fields:\n"
        "{\n"
        '  "decision": "approved|rejected|needs_review",\n'
        '  "compliance": "compliant|non_compliant|needs_review",\n'
        '  "confidence": 0.0,\n'
        '  "basis": "single-sentence basis for the judgment",\n'
        '  "issues": [{"severity":"error|warning|info","category":"...","description":"...","evidence_ref":"..."}],\n'
        '  "evidence": [{"id":"...","type":"...","source":"...","content":"..."}]\n'
        "}\n"
        "Output constraints:\n"
        "- basis must be concise and business-facing.\n"
        "- Invoice number length is not a rejection criterion.\n"
        "- If invoice verification API is unavailable, treat invoices as valid by default in first-gate mode.\n"
        "- If applicant.employee_id != expense_report.employee_id, add a warning for suspected proxy reimbursement.\n"
        "- If key documents are missing or conflicting, set decision=needs_review.\n"
        "- Keep issues/evidence concise and traceable.\n\n"
        f"TASK_ID: {task.task_id}\n"
        "INPUT:\n"
        f"{serialized}\n"
    )


def _build_prompt(task: TaskEnvelope) -> str:
    if task.command == "/audit":
        return _build_audit_prompt(task)
    return f"{task.command} {task.payload}"


def _normalize_issue_item(item: Any, idx: int) -> Dict[str, Any]:
    allowed = {"error", "warning", "info"}
    if isinstance(item, dict):
        severity = _safe_str(item.get("severity"), "warning").lower()
        if severity not in allowed:
            severity = "warning"
        issue = {
            "severity": severity,
            "category": _safe_str(item.get("category"), "general"),
            "description": _safe_str(item.get("description"), "issue reported by model"),
        }
        evidence_ref = item.get("evidence_ref")
        if evidence_ref is not None:
            issue["evidence_ref"] = _safe_str(evidence_ref, f"sdk-issue-{idx}")
        return issue

    return {
        "severity": "warning",
        "category": "general",
        "description": _safe_str(item, "issue reported by model"),
        "evidence_ref": f"sdk-issue-{idx}",
    }


def _normalize_evidence_item(item: Any, idx: int) -> Dict[str, Any]:
    if isinstance(item, dict):
        return {
            "id": _safe_str(item.get("id"), f"sdk-evidence-{idx}"),
            "type": _safe_str(item.get("type"), "text"),
            "source": _safe_str(item.get("source"), "sdk"),
            "content": _safe_str(item.get("content"), ""),
        }

    return {
        "id": f"sdk-evidence-{idx}",
        "type": "text",
        "source": "sdk",
        "content": _safe_str(item, ""),
    }


def _normalize_issues(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [_normalize_issue_item(item, idx) for idx, item in enumerate(value)]


def _normalize_evidence(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [_normalize_evidence_item(item, idx) for idx, item in enumerate(value)]


def _fallback(task: TaskEnvelope, code: str, reason: str, recoverable: bool = True) -> SdkExecutionResult:
    agents = _agents_for_command(task.command)
    if code in {SDK_IMPORT_ERROR, SDK_OPTIONS_ERROR}:
        tool_name = "claude_agent_sdk.init"
        tools_called: List[str] = []
    else:
        tool_name = "claude_agent_sdk.query"
        tools_called = [tool_name]

    events = [
        {"type": "task_start", "data": {"command": task.command}},
        {"type": "agent_dispatch", "data": {"agents": agents, "mode": "serial"}},
        {"type": "task_spawn", "data": {"parallel_tasks": 0}},
        {"type": "tool_call", "data": {"tool": tool_name, "status": "failed", "code": code}},
        {"type": "error", "data": {"code": code, "reason": reason}},
        {"type": "decision_point", "data": {"decision": "needs_review", "confidence": 0.0, "reason": "sdk_fallback"}},
        {"type": "task_end", "data": {"status": "failed"}},
    ]
    envelope = ResultEnvelope(
        task_id=task.task_id,
        command=task.command,
        status="failed",
        result={
            "decision": "needs_review",
            "confidence": 0.0,
            "summary": f"sdk failure: {reason}",
            "issues": [
                {
                    "severity": "error",
                    "category": code,
                    "description": reason,
                    "evidence_ref": "sdk-fallback-001",
                }
            ],
            "evidence": [
                {
                    "id": "sdk-fallback-001",
                    "type": "system",
                    "source": "adapter/sdk_bridge.py",
                    "content": reason,
                }
            ],
        },
        execution={
            "model_used": task.runtime.model or "sonnet",
            "agents_invoked": agents,
            "parallel_tasks": 0,
            "tools_called": tools_called,
        },
        error=error_payload(code, reason, recoverable=recoverable),
    )
    return SdkExecutionResult(envelope=envelope, events=events)


def _normalize_event(message: Any) -> Dict[str, Any]:
    msg_type = getattr(message, "type", None)
    if msg_type is None and isinstance(message, dict):
        msg_type = message.get("type", "unknown")
    if msg_type is None:
        msg_type = "unknown"

    if isinstance(message, dict):
        payload = {k: v for k, v in message.items() if k != "type"}
    else:
        payload = {"repr": repr(message)}

    return {"type": str(msg_type), "data": payload}


def _normalize_decision(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"approved", "rejected", "needs_review"}:
        return text
    return "needs_review"


def _message_to_dict(message: Any) -> Optional[Dict[str, Any]]:
    if isinstance(message, dict):
        return message
    try:
        data = getattr(message, "__dict__", None)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _extract_text(message: Any) -> Optional[str]:
    if isinstance(message, str):
        return message

    if isinstance(message, dict):
        for key in ("result", "text", "content", "summary"):
            value = message.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    for key in ("result", "text", "content", "summary"):
        value = getattr(message, key, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _parse_json_candidate(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None

    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        pass

    block = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if block:
        try:
            data = json.loads(block.group(1))
            return data if isinstance(data, dict) else None
        except Exception:
            pass

    brace = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if brace:
        try:
            data = json.loads(brace.group(1))
            return data if isinstance(data, dict) else None
        except Exception:
            pass

    return None


def _default_result() -> Dict[str, Any]:
    return {
        "decision": "needs_review",
        "confidence": 0.5,
        "summary": "manual review required",
        "issues": [],
        "evidence": [],
    }


def _extract_result_payload(messages: List[Any], command: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    result = _default_result()
    basis = ""

    for msg in messages:
        msg_dict = _message_to_dict(msg)
        candidate: Optional[Dict[str, Any]] = None

        if msg_dict:
            if isinstance(msg_dict.get("result"), dict):
                candidate = msg_dict["result"]
            elif isinstance(msg_dict.get("output"), dict):
                candidate = msg_dict["output"]

        if candidate is None:
            text = _extract_text(msg)
            if text:
                candidate = _parse_json_candidate(text)
                if candidate is None:
                    result["summary"] = _sanitize_basis(text)

        if not candidate:
            continue

        compliance = _safe_str(candidate.get("compliance"), "").lower()
        if compliance in {"compliant", "non_compliant", "needs_review"}:
            if compliance == "compliant":
                result["decision"] = "approved"
            elif compliance == "non_compliant":
                result["decision"] = "rejected"
            else:
                result["decision"] = "needs_review"

        if "compliant" in candidate:
            compliant = candidate.get("compliant")
            if isinstance(compliant, bool):
                result["decision"] = "approved" if compliant else "rejected"

        if "decision" in candidate:
            result["decision"] = _normalize_decision(candidate.get("decision"))

        if "confidence" in candidate:
            try:
                conf = float(candidate.get("confidence"))
                result["confidence"] = max(0.0, min(1.0, conf))
            except Exception:
                pass

        if isinstance(candidate.get("basis"), str) and candidate["basis"].strip():
            basis = candidate["basis"].strip()

        if isinstance(candidate.get("summary"), str) and candidate["summary"].strip():
            result["summary"] = _sanitize_basis(candidate["summary"])

        if "issues" in candidate:
            result["issues"] = _normalize_issues(candidate.get("issues"))

        if "evidence" in candidate:
            result["evidence"] = _normalize_evidence(candidate.get("evidence"))

    if result["confidence"] < 0.7 and result["decision"] != "rejected":
        result["decision"] = "needs_review"

    if basis:
        result["summary"] = _sanitize_basis(basis)
    elif result["issues"]:
        result["summary"] = _sanitize_basis(result["issues"][0].get("description"))
    else:
        result["summary"] = _sanitize_basis(result.get("summary"))

    if command == "/audit":
        _ensure_proxy_reimbursement_warning(result, payload)
        if not result["issues"]:
            severity = "info" if result["decision"] == "approved" else "error" if result["decision"] == "rejected" else "warning"
            result["issues"] = [
                {
                    "severity": severity,
                    "category": "compliance",
                    "description": result["summary"],
                    "evidence_ref": "audit-basis-001",
                }
            ]
        if not result["evidence"]:
            result["evidence"] = [
                {
                    "id": "audit-basis-001",
                    "type": "policy-summary",
                    "source": "ai://claude-audit",
                    "content": result["summary"],
                }
            ]

    return result


async def execute_task_sdk(task: TaskEnvelope) -> SdkExecutionResult:
    try:
        runtime = load_claude_sdk_runtime()
    except Exception as exc:  # pragma: no cover
        return _fallback(task, SDK_IMPORT_ERROR, str(exc), recoverable=False)

    ClaudeAgentOptions = runtime.options_cls
    query = runtime.query_fn

    prompt = _build_prompt(task)
    env = {
        "TASK_ID": task.task_id,
        "TENANT_ID": task.context.tenant_id,
        "OPERATOR_ID": task.context.operator_id,
    }

    base_options: Dict[str, Any] = {
        "cwd": ".",
        "setting_sources": SDK_ACCESS.setting_sources,
        "sandbox": SDK_ACCESS.sandbox,
        "model": task.runtime.model or "sonnet",
        "env": env,
        "allowed_tools": SDK_ACCESS.allowed_tools,
    }
    if SDK_ACCESS.permission_mode:
        base_options["permission_mode"] = SDK_ACCESS.permission_mode

    try:
        # Gracefully add optional fields only when SDK supports them.
        options_payload = dict(base_options)
        for key, value in (("max_tokens", task.runtime.max_tokens), ("timeout_sec", task.runtime.timeout_sec)):
            if not isinstance(value, int) or value <= 0:
                continue
            trial = dict(options_payload)
            trial[key] = value
            try:
                ClaudeAgentOptions(**trial)
                options_payload = trial
            except TypeError:
                continue
        options = ClaudeAgentOptions(**options_payload)
    except Exception as exc:  # pragma: no cover
        return _fallback(task, SDK_OPTIONS_ERROR, f"ClaudeAgentOptions build failed: {exc}", recoverable=False)

    agents = _agents_for_command(task.command)
    raw_messages: List[Any] = []
    events: List[Dict[str, Any]] = [
        {"type": "task_start", "data": {"command": task.command}},
        {"type": "agent_dispatch", "data": {"agents": agents, "mode": "serial"}},
        {"type": "task_spawn", "data": {"parallel_tasks": 0}},
        {
            "type": "tool_call",
            "data": {
                "tool": "claude_agent_sdk.query",
                "status": "started",
                "sdk_module": runtime.module_name,
                "sdk_version": runtime.module_version,
            },
        },
    ]

    try:
        async for message in query(prompt=prompt, options=options):  # pragma: no cover
            raw_messages.append(message)
            events.append(_normalize_event(message))
    except Exception as exc:  # pragma: no cover
        return _fallback(task, SDK_QUERY_ERROR, f"sdk query failed: {exc}", recoverable=True)

    try:
        result_payload = _extract_result_payload(raw_messages, task.command, task.payload)
    except Exception as exc:
        return _fallback(task, SDK_RESULT_MAPPING_ERROR, f"result mapping failed: {exc}", recoverable=True)

    events.append({"type": "tool_call", "data": {"tool": "claude_agent_sdk.query", "status": "completed", "message_count": len(raw_messages)}})
    events.append(
        {
            "type": "decision_point",
            "data": {"decision": result_payload.get("decision"), "confidence": result_payload.get("confidence")},
        }
    )
    events.append({"type": "task_end", "data": {"status": "completed"}})

    envelope = ResultEnvelope(
        task_id=task.task_id,
        command=task.command,
        status="completed",
        result=result_payload,
        execution={
            "model_used": task.runtime.model or "sonnet",
            "agents_invoked": agents,
            "parallel_tasks": 0,
            "tools_called": ["claude_agent_sdk.query"],
        },
        error=None,
    )
    return SdkExecutionResult(envelope=envelope, events=events)


def execute_task(task: TaskEnvelope) -> SdkExecutionResult:
    timeout_sec = task.runtime.timeout_sec if isinstance(task.runtime.timeout_sec, int) and task.runtime.timeout_sec > 0 else 300

    async def _run_with_timeout() -> SdkExecutionResult:
        return await asyncio.wait_for(execute_task_sdk(task), timeout=timeout_sec)

    try:
        return asyncio.run(_run_with_timeout())
    except TimeoutError:
        return _fallback(
            task,
            SDK_QUERY_ERROR,
            f"sdk execution timeout after {timeout_sec}s",
            recoverable=True,
        )
    except RuntimeError as exc:
        # Only downgrade to fallback for the known nested-loop case.
        if "asyncio.run() cannot be called from a running event loop" not in str(exc):
            raise
        return _fallback(
            task,
            SDK_EVENT_LOOP_ERROR,
            "event loop already running; use execute_task_sdk() in async context",
            recoverable=True,
        )
