"""Redis store backend for adapter persistence.

Uses redis-py for event caching and task meta hot lookups.
Falls through to an inner memory store for full task/result CRUD.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .store import StoreBackend
from .store_memory import MemoryStoreBackend

logger = logging.getLogger("adapter.store_redis")

_PREFIX = "adapter:"


class RedisStoreBackend(StoreBackend):
    """Redis-backed store with in-memory fallback for task/result CRUD.

    Redis is used primarily for:
    - Events (sorted set per task_id, timestamp as score)
    - Task meta (hash per task_id)
    - History logs (list)

    Task envelopes and result envelopes are stored in the inner memory
    backend for simplicity; switch to PostgresStoreBackend for fully
    durable task storage.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        try:
            import redis as redis_lib  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "redis is required for redis backend: pip install redis"
            ) from exc

        url = config.get("url", "redis://localhost:6379/0")
        self._ttl = int(config.get("event_ttl_seconds", 86400))
        self._r = redis_lib.Redis.from_url(url, decode_responses=True)
        self._inner = MemoryStoreBackend()

        try:
            self._r.ping()
            logger.info("redis connected: %s", url)
        except Exception:
            logger.exception("redis connection failed: %s", url)
            raise

    def _key(self, *parts: str) -> str:
        return _PREFIX + ":".join(parts)

    # ── Task envelope (delegated to inner) ──

    def save_task(self, task_id: str, envelope: Dict[str, Any]) -> None:
        self._inner.save_task(task_id, envelope)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._inner.get_task(task_id)

    def has_task(self, task_id: str) -> bool:
        return self._inner.has_task(task_id)

    # ── Result envelope (delegated to inner) ──

    def save_result(self, task_id: str, result: Dict[str, Any]) -> None:
        self._inner.save_result(task_id, result)

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._inner.get_result(task_id)

    def has_result(self, task_id: str) -> bool:
        return self._inner.has_result(task_id)

    # ── Task meta (Redis hash) ──

    def save_meta(self, task_id: str, meta: Dict[str, Any]) -> None:
        self._inner.save_meta(task_id, meta)
        key = self._key("meta", task_id)
        flat = {k: json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                for k, v in meta.items() if v is not None}
        if flat:
            self._r.hset(key, mapping=flat)
            if self._ttl > 0:
                self._r.expire(key, self._ttl)

    def get_meta(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._inner.get_meta(task_id)

    def list_meta(
        self,
        *,
        command: Optional[str] = None,
        tenant_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        return self._inner.list_meta(
            command=command,
            tenant_id=tenant_id,
            operator_id=operator_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    # ── Events (Redis sorted set) ──

    def save_event(self, task_id: str, event: Dict[str, Any]) -> None:
        self._inner.save_event(task_id, event)
        key = self._key("events", task_id)
        ts = event.get("timestamp", datetime.now(timezone.utc).isoformat())
        try:
            score = datetime.fromisoformat(ts).timestamp()
        except (ValueError, TypeError):
            score = datetime.now(timezone.utc).timestamp()
        self._r.zadd(key, {json.dumps(event, ensure_ascii=False): score})
        if self._ttl > 0:
            self._r.expire(key, self._ttl)

    def list_events(self, task_id: str) -> List[Dict[str, Any]]:
        key = self._key("events", task_id)
        raw = self._r.zrange(key, 0, -1)
        if raw:
            events = []
            for item in raw:
                try:
                    events.append(json.loads(item))
                except (json.JSONDecodeError, TypeError):
                    continue
            return events
        return self._inner.list_events(task_id)

    def delete_events(self, task_id: str) -> int:
        count = self._inner.delete_events(task_id)
        key = self._key("events", task_id)
        redis_count = self._r.delete(key)
        return max(count, redis_count)

    # ── History logs (Redis list) ──

    def save_history(self, record: Dict[str, Any]) -> None:
        self._inner.save_history(record)
        key = self._key("history")
        self._r.rpush(key, json.dumps(record, ensure_ascii=False))

    def list_history(
        self, *, task_id: Optional[str] = None, limit: int = 200
    ) -> List[Dict[str, Any]]:
        return self._inner.list_history(task_id=task_id, limit=limit)

    # ── Cascade delete ──

    def delete_task(self, task_id: str) -> Dict[str, bool]:
        result = self._inner.delete_task(task_id)
        self._r.delete(self._key("meta", task_id))
        self._r.delete(self._key("events", task_id))
        return result

    # ── Lifecycle ──

    def close(self) -> None:
        try:
            self._r.close()
        except Exception:
            pass
