"""Runtime configuration for v4 adapter plane."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterConfig:
    max_concurrent_sessions: int = 3
    default_timeout_sec: int = 300
    max_events_per_task: int = 200


DEFAULT_CONFIG = AdapterConfig()
