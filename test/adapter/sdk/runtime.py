"""Runtime loader for model backends.

Supports:
- Anthropic Messages API (default).
- Anthropic-compatible HTTP endpoint (local/private), enabled when
  ADAPTER_LLM_BASE_URL or LOCAL_LLM_BASE_URL is set.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

_client: Any = None


@dataclass(frozen=True)
class ModelRuntime:
    provider: str  # "anthropic" | "anthropic_messages_http"
    client: Any
    model: str
    max_tokens: int
    module_name: str
    module_version: str
    timeout_sec: int
    max_retries: int
    base_url: Optional[str] = None


# Backward-compatible alias.
AnthropicRuntime = ModelRuntime


def _get_model() -> str:
    model = os.getenv("ADAPTER_LLM_MODEL", "").strip()
    if model:
        return model
    legacy = os.getenv("ADAPTER_CLAUDE_MODEL", "").strip()
    if legacy:
        return legacy
    return "claude-sonnet-4-20250514"


def _get_timeout() -> int:
    try:
        return int(os.getenv("ADAPTER_CLAUDE_TIMEOUT", "120"))
    except (ValueError, TypeError):
        return 120


def _get_max_retries() -> int:
    try:
        return int(os.getenv("ADAPTER_CLAUDE_MAX_RETRIES", "2"))
    except (ValueError, TypeError):
        return 2


def _get_messages_base_url() -> str:
    return (
        os.getenv("ADAPTER_LLM_BASE_URL", "").strip()
        or os.getenv("LOCAL_LLM_BASE_URL", "").strip()
    )


def is_messages_http_enabled() -> bool:
    return bool(_get_messages_base_url())


def normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def get_messages_url(base_url: str) -> str:
    normalized = normalize_base_url(base_url)
    if normalized.endswith("/messages"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/messages"
    return f"{normalized}/v1/messages"


def load_anthropic_runtime(
    *,
    model: Optional[str] = None,
    max_tokens: int = 8192,
) -> ModelRuntime:
    """Load Anthropic SDK runtime — lazy-creates a shared client singleton."""
    global _client

    try:
        import anthropic
    except ImportError as exc:
        raise ImportError(
            "anthropic package not installed. Run: pip install anthropic"
        ) from exc

    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key or api_key == "dummy":
            raise ImportError(
                "ANTHROPIC_API_KEY not set or is 'dummy'. "
                "Set a valid key, or configure ADAPTER_LLM_BASE_URL for local Anthropic-compatible endpoints."
            )
        _client = anthropic.Anthropic(
            api_key=api_key,
            timeout=float(_get_timeout()),
            max_retries=_get_max_retries(),
        )

    version = "unknown"
    try:
        import anthropic as _anth
        version = getattr(_anth, "__version__", "unknown")
    except Exception:
        pass

    resolved_model = model or _get_model()
    return ModelRuntime(
        provider="anthropic",
        client=_client,
        model=resolved_model,
        max_tokens=max_tokens,
        module_name="anthropic",
        module_version=str(version),
        timeout_sec=_get_timeout(),
        max_retries=_get_max_retries(),
        base_url=None,
    )


def load_runtime(
    *,
    model: Optional[str] = None,
    max_tokens: int = 8192,
) -> ModelRuntime:
    """Load model runtime based on environment configuration."""
    base_url = _get_messages_base_url()
    resolved_model = model or _get_model()

    if base_url:
        return ModelRuntime(
            provider="anthropic_messages_http",
            client=None,
            model=resolved_model,
            max_tokens=max_tokens,
            module_name="anthropic-messages-http",
            module_version="1",
            timeout_sec=_get_timeout(),
            max_retries=_get_max_retries(),
            base_url=normalize_base_url(base_url),
        )

    return load_anthropic_runtime(model=resolved_model, max_tokens=max_tokens)


def reset_client() -> None:
    """Reset the cached client — for tests only."""
    global _client
    _client = None
