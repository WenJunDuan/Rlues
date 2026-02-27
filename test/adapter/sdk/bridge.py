"""SDK bridge for Anthropic Messages API integration."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.error_codes import (
    SDK_IMPORT_ERROR,
    SDK_OPTIONS_ERROR,
    SDK_QUERY_ERROR,
    SDK_RESULT_MAPPING_ERROR,
    error_payload,
)
from ..core.types import ResultEnvelope, TaskEnvelope

logger = logging.getLogger("adapter.sdk.bridge")


@dataclass
class SdkExecutionResult:
    envelope: ResultEnvelope
    events: List[Dict[str, Any]]


COMMAND_AGENT_MAP = {
    "/audit": ["expense-auditor"],
}

_RESULT_KEYS = {"decision", "confidence", "summary", "issues", "evidence"}

# ─── Agent prompt loading ──────────────────────────────────

_AGENTS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "agents"
_SKILLS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "skills"
_AUDIT_RULE_FILES = (
    "amount-check.md",
    "duplicate-detect.md",
    "category-match.md",
    "invoice-authenticity.md",
    "tax-compliance.md",
)


def _load_agent_prompt(command: str) -> str:
    """Load system prompt from .claude/agents/*.md for the given command."""
    agent_map = {
        "/audit": "expense-auditor.md",
    }
    agent_file = agent_map.get(command)
    if agent_file:
        path = _AGENTS_DIR / agent_file
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                logger.warning("Failed to read agent prompt: %s", path)

    return (
        "你是企业费用审核专家。根据提供的报销单据和公司规则，逐项审核并输出结构化结论。"
        "必须返回 JSON 格式，包含 decision/confidence/summary/issues/evidence 字段。"
    )


def _load_skill_rules(command: str) -> str:
    """Load skill rules as supplementary context for the system prompt."""
    if command != "/audit":
        return ""

    rules_dir = _SKILLS_DIR / "expense-audit" / "rules"
    if not rules_dir.exists():
        return ""

    parts: List[str] = []
    for name in _AUDIT_RULE_FILES:
        rule_file = rules_dir / name
        if not rule_file.exists():
            continue
        try:
            content = rule_file.read_text(encoding="utf-8")
            parts.append(f"## Rule: {rule_file.stem}\n\n{content}")
        except Exception:
            continue

    return "\n\n---\n\n".join(parts)


# ─── Helper functions ──────────────────────────────────────

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


def _build_user_message(task: TaskEnvelope) -> str:
    """Build the user message from a TaskEnvelope."""
    try:
        payload_blob = json.dumps(task.payload, ensure_ascii=False, indent=2)
    except TypeError:
        payload_blob = str(task.payload)

    return (
        f"请审核以下报销单据（command: {task.command}）：\n\n"
        f"Task ID: {task.task_id}\n"
        f"Tenant: {task.context.tenant_id}\n"
        f"Operator: {task.context.operator_id}\n\n"
        f"```json\n{payload_blob}\n```\n\n"
        f"请按照输出契约返回 JSON 格式的审核结论。"
    )


# ─── Fallback path ─────────────────────────────────────────

def _tool_name_for_provider(provider: str) -> str:
    return "anthropic.messages.create"


def _fallback(
    task: TaskEnvelope,
    code: str,
    reason: str,
    recoverable: bool = True,
    *,
    tool_name: Optional[str] = None,
    model_used: Optional[str] = None,
) -> SdkExecutionResult:
    agents = _agents_for_command(task.command)
    chosen_tool_name = tool_name or "anthropic.messages.create"
    if code in {SDK_IMPORT_ERROR, SDK_OPTIONS_ERROR}:
        tools_called: List[str] = []
    else:
        tools_called = [chosen_tool_name]

    events = [
        {"type": "task_start", "data": {"command": task.command}},
        {"type": "agent_dispatch", "data": {"agents": agents, "mode": "serial"}},
        {"type": "task_spawn", "data": {"parallel_tasks": 0}},
        {"type": "tool_call", "data": {"tool": chosen_tool_name, "status": "failed", "code": code}},
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
            "model_used": model_used or task.runtime.model or "sonnet",
            "agents_invoked": agents,
            "parallel_tasks": 0,
            "tools_called": tools_called,
        },
        error=error_payload(code, reason, recoverable=recoverable),
    )
    return SdkExecutionResult(envelope=envelope, events=events)


# ─── Result normalization ──────────────────────────────────

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


def _normalize_decision(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"approved", "rejected", "needs_review"}:
        return text
    return "needs_review"


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


def _extract_result_from_text(text: str) -> Dict[str, Any]:
    """Extract structured result from Claude's response text."""
    parsed = _parse_json_candidate(text)
    if isinstance(parsed, dict) and _RESULT_KEYS.intersection(parsed.keys()):
        return _normalize_result_payload(parsed, "manual review required")

    return _default_result(_sanitize_summary(text))


def _extract_messages_text(payload: Dict[str, Any]) -> str:
    content = payload.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list) or not content:
        return ""
    parts: List[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "text":
            continue
        text = item.get("text")
        if isinstance(text, str) and text:
            parts.append(text)
    return "".join(parts)


def _call_messages_http(
    *,
    base_url: str,
    model: str,
    max_tokens: int,
    system_prompt: str,
    user_message: str,
    timeout_sec: int,
    max_retries: int = 2,
) -> Dict[str, Any]:
    import time
    from .runtime import get_messages_url

    url = get_messages_url(base_url)
    request_payload = {
        "model": model,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
        "max_tokens": max_tokens,
    }

    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    api_key = (
        os.getenv("ADAPTER_LLM_API_KEY", "").strip()
        or os.getenv("ANTHROPIC_API_KEY", "").strip()
    )
    if api_key and api_key != "dummy":
        headers["x-api-key"] = api_key

    data = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")

    last_exc: Optional[Exception] = None
    for attempt in range(1 + max(0, max_retries)):
        request = urllib.request.Request(url=url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout_sec) as response:
                raw = response.read().decode("utf-8", errors="replace")
                status = response.getcode()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code in (429, 500, 502, 503, 529) and attempt < max_retries:
                wait = min(2 ** attempt, 8)
                logger.warning("messages-http %d (attempt %d/%d), retrying in %ds", exc.code, attempt + 1, 1 + max_retries, wait)
                time.sleep(wait)
                last_exc = RuntimeError(f"messages-http {exc.code}: {body[:500]}")
                continue
            raise RuntimeError(f"messages-http {exc.code}: {body[:500]}") from exc
        except urllib.error.URLError as exc:
            if attempt < max_retries:
                wait = min(2 ** attempt, 8)
                logger.warning("messages-http network error (attempt %d/%d), retrying in %ds: %s", attempt + 1, 1 + max_retries, wait, exc)
                time.sleep(wait)
                last_exc = RuntimeError(f"messages-http network error: {exc}")
                continue
            raise RuntimeError(f"messages-http network error: {exc}") from exc
        else:
            # Success path
            if status >= 400:
                raise RuntimeError(f"messages-http status {status}: {raw[:500]}")

            try:
                payload = json.loads(raw)
            except Exception as exc:
                raise RuntimeError(f"messages-http invalid json response: {raw[:300]}") from exc

            if not isinstance(payload, dict):
                raise RuntimeError("messages-http response is not a JSON object")

            return payload

    # Should not reach here, but just in case
    raise last_exc or RuntimeError("messages-http: all retries exhausted")


# ─── Core execution: Anthropic Messages API ───────────────

def execute_task(task: TaskEnvelope) -> SdkExecutionResult:
    """Execute a task using the Anthropic Messages API (synchronous).

    This is the main entry point called by scheduler._drain_session_worker.
    """
    # 1. Load runtime (lazy init, provider-aware)
    try:
        from .runtime import load_runtime
        runtime = load_runtime(
            model=task.runtime.model,
            max_tokens=task.runtime.max_tokens,
        )
    except ImportError as exc:
        return _fallback(task, SDK_IMPORT_ERROR, str(exc), recoverable=False)
    except Exception as exc:
        return _fallback(task, SDK_IMPORT_ERROR, f"runtime init failed: {exc}", recoverable=False)

    client = runtime.client
    provider = runtime.provider
    model = runtime.model
    max_tokens = runtime.max_tokens
    tool_name = _tool_name_for_provider(provider)
    agents = _agents_for_command(task.command)

    # 2. Build system prompt from .claude/agents/*.md + skill rules
    system_prompt = _load_agent_prompt(task.command)
    skill_rules = _load_skill_rules(task.command)
    if skill_rules:
        system_prompt = f"{system_prompt}\n\n# Audit Rules\n\n{skill_rules}"

    # Append output format instruction
    system_prompt += (
        "\n\n# Output Format\n\n"
        "你必须返回一个 JSON 对象，包含以下字段：\n"
        "- decision: \"approved\" | \"rejected\" | \"needs_review\"\n"
        "- confidence: 0.0 到 1.0 之间的浮点数\n"
        "- summary: 一句话总结审核结论\n"
        "- issues: [{severity, category, description, evidence_ref?}]\n"
        "- evidence: [{id, type, source, content}]\n\n"
        "只返回 JSON，不要包含其他文字。"
    )

    # 3. Build user message
    user_message = _build_user_message(task)

    # 4. Events tracking
    events: List[Dict[str, Any]] = [
        {"type": "task_start", "data": {"command": task.command}},
        {"type": "agent_dispatch", "data": {"agents": agents, "mode": "serial"}},
        {"type": "task_spawn", "data": {"parallel_tasks": 0}},
        {
            "type": "tool_call",
            "data": {
                "tool": tool_name,
                "status": "started",
                "sdk_module": runtime.module_name,
                "sdk_version": runtime.module_version,
                "model": model,
            },
        },
    ]

    # 5. Call model backend
    try:
        response_text = ""
        model_used = model
        input_tokens: Optional[int] = None
        output_tokens: Optional[int] = None
        stop_reason: Optional[str] = None

        if provider == "anthropic":
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            model_used = str(getattr(response, "model", model))
            stop_reason = str(getattr(response, "stop_reason", ""))
            usage = getattr(response, "usage", None)
            if usage is not None:
                input_tokens = getattr(usage, "input_tokens", None)
                output_tokens = getattr(usage, "output_tokens", None)
            for block in response.content:
                if hasattr(block, "text"):
                    response_text += block.text
        elif provider == "anthropic_messages_http":
            payload = _call_messages_http(
                base_url=runtime.base_url or "",
                model=model,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                user_message=user_message,
                timeout_sec=runtime.timeout_sec,
                max_retries=runtime.max_retries,
            )
            response_text = _extract_messages_text(payload)
            model_used = str(payload.get("model") or model)
            usage_blob = payload.get("usage")
            if isinstance(usage_blob, dict):
                input_tokens = usage_blob.get("input_tokens")
                output_tokens = usage_blob.get("output_tokens")
            stop_reason = str(payload.get("stop_reason") or "")
        else:
            raise RuntimeError(f"unsupported runtime provider: {provider}")
    except Exception as exc:
        logger.error("Model API call failed for task %s: %s", task.task_id, exc)
        return _fallback(
            task,
            SDK_QUERY_ERROR,
            f"{provider} api call failed: {exc}",
            recoverable=True,
            tool_name=tool_name,
            model_used=model,
        )

    # 6. Record completed tool call event
    events.append(
        {
            "type": "tool_call",
            "data": {
                "tool": tool_name,
                "status": "completed",
                "model": model_used,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
                "stop_reason": stop_reason,
            },
        }
    )

    # 7. Parse structured result from response text
    try:
        result_payload = _extract_result_from_text(response_text)
    except Exception as exc:
        return _fallback(
            task,
            SDK_RESULT_MAPPING_ERROR,
            f"result mapping failed: {exc}",
            recoverable=True,
            tool_name=tool_name,
            model_used=model,
        )

    # 8. Apply decision logic
    decision = _normalize_decision(result_payload.get("decision"))
    confidence = result_payload.get("confidence")
    if _is_number(confidence) and float(confidence) < 0.7 and decision != "rejected":
        decision = "needs_review"
    result_payload["decision"] = decision

    envelope_status = "needs_review" if decision == "needs_review" else "completed"

    events.append({
        "type": "decision_point",
        "data": {"decision": decision, "confidence": result_payload.get("confidence")},
    })
    events.append({"type": "task_end", "data": {"status": envelope_status}})

    # 9. Build result envelope
    envelope = ResultEnvelope(
        task_id=task.task_id,
        command=task.command,
        status=envelope_status,
        result=result_payload,
        execution={
            "model_used": model_used,
            "agents_invoked": agents,
            "parallel_tasks": 0,
            "tools_called": [tool_name],
        },
        error=None,
    )
    return SdkExecutionResult(envelope=envelope, events=events)
