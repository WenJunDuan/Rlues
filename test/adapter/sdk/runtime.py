"""Runtime loader for Claude official Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ClaudeSdkRuntime:
    options_cls: Any
    query_fn: Callable[..., Any]
    module_name: str
    module_version: str


def load_claude_sdk_runtime() -> ClaudeSdkRuntime:
    """Load Claude SDK runtime from the official `claude-agent-sdk` package."""
    try:
        import claude_agent_sdk as sdk  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise ImportError(f"claude_agent_sdk import failed: {exc}") from exc

    options_cls = getattr(sdk, "ClaudeAgentOptions", None)
    query_fn = getattr(sdk, "query", None)
    if options_cls is None or query_fn is None:  # pragma: no cover
        raise ImportError("claude_agent_sdk missing required symbols: ClaudeAgentOptions/query")

    version = getattr(sdk, "__version__", "unknown")
    return ClaudeSdkRuntime(
        options_cls=options_cls,
        query_fn=query_fn,
        module_name="claude_agent_sdk",
        module_version=str(version),
    )
