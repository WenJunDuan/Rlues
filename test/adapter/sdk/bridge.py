"""SDK bridge for claude_agent_sdk integration.

This module provides a real SDK integration path and a safe fallback path.
It is not executed in this phase.
"""

from __future__ import annotations

import asyncio
import json
import threading
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
from ..core.types import ResultEnvelope, TaskEnvelope
from .access import SDK_ACCESS
from .runtime import load_claude_sdk_runtime


@dataclass
class SdkExecutionResult:
    envelope: ResultEnvelope
    events: List[Dict[str, Any]]


COMMAND_AGENT_MAP = {
    "/audit": ["expense-auditor"],
}

_RESULT_KEYS = {"decision", "confidence", "summary", "issues", "evidence"}
_THREAD_LOCAL = threading.local()


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _sanitize_summary(value: Any, default: str = "manual review required") -> str:
    text = _safe_str(value, default=default)
    if not text:
        return default
    return " ".join(text.split())[:180]


def _is_number(value: Any) -> bool:
    return (isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)


def _agents_for_command(command: str) -> List[str]:
    return COMMAND_AGENT_MAP.get(command, ["orchestrator-fallback"])


def _build_prompt(task: TaskEnvelope) -> str:
    try:
        payload_blob = json.dumps(task.payload, ensure_ascii=False)
    except TypeError:
        payload_blob = str(task.payload)
    return f"{task.command} {payload_blob}"


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
                    "source": "adapter/sdk/bridge.py",
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
    except Exception:
        return None
    return data if isinstance(data, dict) else None


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


def _looks_like_result_payload(candidate: Any) -> bool:
    return isinstance(candidate, dict) and bool(_RESULT_KEYS.intersection(candidate.keys()))


def _candidate_from_message(message: Any) -> Optional[Dict[str, Any]]:
    msg_dict = _message_to_dict(message)
    if not isinstance(msg_dict, dict):
        return None

    if _looks_like_result_payload(msg_dict):
        return msg_dict

    result_field = msg_dict.get("result")
    if _looks_like_result_payload(result_field):
        return result_field

    output_field = msg_dict.get("output")
    if _looks_like_result_payload(output_field):
        return output_field

    return None


def _parse_json_candidate(text: str) -> Optional[Dict[str, Any]]:
    content = text.strip()
    if not content:
        return None

    try:
        data = json.loads(content)
        return data if isinstance(data, dict) else None
    except Exception:
        pass

    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end <= start:
        return None

    try:
        data = json.loads(content[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _default_result(summary: str = "manual review required") -> Dict[str, Any]:
    return {
        "decision": "needs_review",
        "confidence": 0.0,
        "summary": _sanitize_summary(summary),
        "issues": [],
        "evidence": [],
    }


def _normalize_result_payload(candidate: Dict[str, Any], fallback_summary: str) -> Dict[str, Any]:
    result = _default_result(fallback_summary)

    if "decision" in candidate:
        result["decision"] = _normalize_decision(candidate.get("decision"))

    confidence = candidate.get("confidence")
    if _is_number(confidence):
        result["confidence"] = max(0.0, min(1.0, float(confidence)))

    summary = candidate.get("summary")
    if isinstance(summary, str) and summary.strip():
        result["summary"] = _sanitize_summary(summary)
    else:
        basis = candidate.get("basis")
        if isinstance(basis, str) and basis.strip():
            result["summary"] = _sanitize_summary(basis)

    if "issues" in candidate:
        result["issues"] = _normalize_issues(candidate.get("issues"))

    if "evidence" in candidate:
        result["evidence"] = _normalize_evidence(candidate.get("evidence"))

    return result


def _extract_result_payload(messages: List[Any]) -> Dict[str, Any]:
    fallback_summary = "manual review required"

    for message in reversed(messages):
        candidate = _candidate_from_message(message)
        if isinstance(candidate, dict):
            return _normalize_result_payload(candidate, fallback_summary)

        text = _extract_text(message)
        if not text:
            continue

        parsed = _parse_json_candidate(text)
        if isinstance(parsed, dict):
            return _normalize_result_payload(parsed, fallback_summary)

        fallback_summary = _sanitize_summary(text)

    return _default_result(fallback_summary)


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
        result_payload = _extract_result_payload(raw_messages)
    except Exception as exc:
        return _fallback(task, SDK_RESULT_MAPPING_ERROR, f"result mapping failed: {exc}", recoverable=True)

    decision = _normalize_decision(result_payload.get("decision"))
    confidence = result_payload.get("confidence")
    if _is_number(confidence) and float(confidence) < 0.7 and decision != "rejected":
        decision = "needs_review"
    result_payload["decision"] = decision

    envelope_status = "needs_review" if decision == "needs_review" else "completed"

    events.append({"type": "tool_call", "data": {"tool": "claude_agent_sdk.query", "status": "completed", "message_count": len(raw_messages)}})
    events.append(
        {
            "type": "decision_point",
            "data": {"decision": decision, "confidence": result_payload.get("confidence")},
        }
    )
    events.append({"type": "task_end", "data": {"status": envelope_status}})

    envelope = ResultEnvelope(
        task_id=task.task_id,
        command=task.command,
        status=envelope_status,
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


def _get_thread_loop() -> asyncio.AbstractEventLoop:
    loop = getattr(_THREAD_LOCAL, "loop", None)
    if isinstance(loop, asyncio.AbstractEventLoop) and not loop.is_closed():
        return loop

    loop = asyncio.new_event_loop()
    _THREAD_LOCAL.loop = loop
    return loop


def execute_task(task: TaskEnvelope) -> SdkExecutionResult:
    timeout_sec = task.runtime.timeout_sec if isinstance(task.runtime.timeout_sec, int) and task.runtime.timeout_sec > 0 else 300

    loop = _get_thread_loop()
    if loop.is_running():
        return _fallback(
            task,
            SDK_EVENT_LOOP_ERROR,
            "thread-local event loop already running; use execute_task_sdk() in async context",
            recoverable=True,
        )

    try:
        return loop.run_until_complete(asyncio.wait_for(execute_task_sdk(task), timeout=timeout_sec))
    except asyncio.TimeoutError:
        return _fallback(
            task,
            SDK_QUERY_ERROR,
            f"sdk execution timeout after {timeout_sec}s",
            recoverable=True,
        )
    except RuntimeError as exc:
        return _fallback(
            task,
            SDK_EVENT_LOOP_ERROR,
            f"event loop runtime error: {exc}",
            recoverable=True,
        )
    finally:
        # P1-6: Close the thread-local event loop to prevent fd leaks
        # when thread pool threads are recycled.
        try:
            loop.close()
        except Exception:
            pass
        _THREAD_LOCAL.loop = None
