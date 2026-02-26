"""Persistence configuration loader.

Loads adapter/persistence.yaml with env-var overrides.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class PostgresConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "adapter"
    user: str = "adapter"
    password: str = ""
    pool_size: int = 5


@dataclass(frozen=True)
class RedisConfig:
    url: str = "redis://localhost:6379/0"
    event_ttl_seconds: int = 86400


@dataclass(frozen=True)
class PersistenceConfig:
    backend: str = "memory"
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend,
            "postgres": {
                "host": self.postgres.host,
                "port": self.postgres.port,
                "database": self.postgres.database,
                "user": self.postgres.user,
                "password": self.postgres.password,
                "pool_size": self.postgres.pool_size,
            },
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
    """Load persistence config from YAML file + env overrides."""

    default_path = Path(__file__).resolve().parents[1] / "persistence.yaml"
    config_path = Path(os.getenv("ADAPTER_PERSISTENCE_CONFIG", str(default_path)))

    raw: Dict[str, Any] = {}
    if config_path.exists():
        try:
            import yaml  # type: ignore

            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except ImportError:
            # Fallback: parse simple YAML-like key: value pairs
            raw = _parse_simple_yaml(config_path)
        except Exception:
            raw = {}

    if not isinstance(raw, dict):
        raw = {}

    # Backend
    backend = _str_env("ADAPTER_STORE_BACKEND") or str(raw.get("backend", "memory")).strip()
    if backend not in {"memory", "postgres", "redis"}:
        backend = "memory"

    # Postgres
    pg_raw = raw.get("postgres", {})
    if not isinstance(pg_raw, dict):
        pg_raw = {}
    pg = PostgresConfig(
        host=_str_env("ADAPTER_PG_HOST") or str(pg_raw.get("host", "localhost")),
        port=_int_env("ADAPTER_PG_PORT") or int(pg_raw.get("port", 5432)),
        database=_str_env("ADAPTER_PG_DATABASE") or str(pg_raw.get("database", "adapter")),
        user=_str_env("ADAPTER_PG_USER") or str(pg_raw.get("user", "adapter")),
        password=_str_env("ADAPTER_PG_PASSWORD") or str(pg_raw.get("password", "")),
        pool_size=_int_env("ADAPTER_PG_POOL_SIZE") or int(pg_raw.get("pool_size", 5)),
    )

    # Redis
    redis_raw = raw.get("redis", {})
    if not isinstance(redis_raw, dict):
        redis_raw = {}
    redis_cfg = RedisConfig(
        url=_str_env("ADAPTER_REDIS_URL") or str(redis_raw.get("url", "redis://localhost:6379/0")),
        event_ttl_seconds=_int_env("ADAPTER_REDIS_EVENT_TTL") or int(redis_raw.get("event_ttl_seconds", 86400)),
    )

    return PersistenceConfig(backend=backend, postgres=pg, redis=redis_cfg)


def _parse_simple_yaml(path: Path) -> Dict[str, Any]:
    """Minimal YAML parser for flat key: value pairs (no nested blocks)."""
    result: Dict[str, Any] = {}
    current_section: Optional[str] = None
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" in stripped and not stripped.startswith(" ") and not stripped.startswith("\t"):
                key, _, value = stripped.partition(":")
                value = value.strip().strip('"').strip("'")
                if value:
                    result[key.strip()] = value
                else:
                    current_section = key.strip()
                    result[current_section] = {}
            elif current_section and (":" in stripped):
                key, _, value = stripped.partition(":")
                value = value.strip().strip('"').strip("'")
                section = result.get(current_section)
                if isinstance(section, dict):
                    section[key.strip()] = value
    except Exception:
        pass
    return result


PERSISTENCE_CONFIG = load_persistence_config()
