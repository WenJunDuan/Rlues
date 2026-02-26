"""Adapter default runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    max_concurrent_sessions: int = 4
    default_timeout_sec: int = 120
    max_events_per_task: int = 200


DEFAULT_CONFIG = RuntimeConfig()
