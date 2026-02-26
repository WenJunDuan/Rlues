"""Persistence configuration loader.

Loads persistence config from unified JSON config file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .config_loader import load_adapter_config


@dataclass(frozen=True)
class RedisConfig:
    url: str = "redis://localhost:6379/0"
    event_ttl_seconds: int = 86400


@dataclass(frozen=True)
class PersistenceConfig:
    backend: str = "memory"
    redis: RedisConfig = field(default_factory=RedisConfig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend,
            "redis": {
                "url": self.redis.url,
                "event_ttl_seconds": self.redis.event_ttl_seconds,
            },
        }


def _str_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is not None:
        stripped = value.strip()
        return stripped if stripped else None
    return None


def _int_env(name: str) -> Optional[int]:
    value = os.getenv(name)
    if value is None:
        return None
    try:
        return int(value.strip())
    except (ValueError, TypeError):
        return None


def load_persistence_config() -> PersistenceConfig:
    """Load persistence config from unified JSON config + env overrides."""

    root = load_adapter_config().data
    persistence_raw = root.get("persistence")
    if isinstance(persistence_raw, dict):
        raw = persistence_raw
    elif any(key in root for key in ("backend", "redis")):
        # Backward compatible with legacy persistence-only config shape.
        raw = root
    else:
        raw = {}

    backend = _str_env("ADAPTER_STORE_BACKEND") or str(raw.get("backend", "memory")).strip()
    if backend not in {"memory", "redis"}:
        backend = "memory"

    redis_raw = raw.get("redis", {})
    if not isinstance(redis_raw, dict):
        redis_raw = {}
    redis_cfg = RedisConfig(
        url=_str_env("ADAPTER_REDIS_URL") or str(redis_raw.get("url", "redis://localhost:6379/0")),
        event_ttl_seconds=_int_env("ADAPTER_REDIS_EVENT_TTL") or int(redis_raw.get("event_ttl_seconds", 86400)),
    )

    return PersistenceConfig(backend=backend, redis=redis_cfg)


PERSISTENCE_CONFIG = load_persistence_config()
