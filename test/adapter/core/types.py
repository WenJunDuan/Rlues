"""Core data types for v4 adapter minimal runnable chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TaskContext:
    tenant_id: str
    operator_id: str
    session_id: Optional[str] = None


@dataclass
class RuntimeOptions:
    model: Optional[str] = None
    max_tokens: int = 8192
    timeout_sec: int = 300
    trace_id: Optional[str] = None
    rules_version: Optional[str] = None


@dataclass
class TaskEnvelope:
    task_id: str
    command: str
    context: TaskContext
    payload: Dict[str, Any] = field(default_factory=dict)
    runtime: RuntimeOptions = field(default_factory=RuntimeOptions)


@dataclass
class ResultEnvelope:
    task_id: str
    command: str
    status: str
    result: Dict[str, Any]
    execution: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None


def from_dict(data: Dict[str, Any]) -> TaskEnvelope:
    ctx = data.get("context", {})
    runtime = data.get("runtime", {})
    return TaskEnvelope(
        task_id=data["task_id"],
        command=data["command"],
        context=TaskContext(
            tenant_id=ctx["tenant_id"],
            operator_id=ctx["operator_id"],
            session_id=ctx.get("session_id"),
        ),
        payload=data.get("payload", {}),
        runtime=RuntimeOptions(
            model=runtime.get("model"),
            max_tokens=runtime.get("max_tokens", 8192),
            timeout_sec=runtime.get("timeout_sec", 300),
            trace_id=runtime.get("trace_id"),
            rules_version=runtime.get("rules_version"),
        ),
    )
