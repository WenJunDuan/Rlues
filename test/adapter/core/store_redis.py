"""Redis store backend for adapter persistence.

Redis is the source of truth for cross-process readability.
An inner memory store is kept as a best-effort local cache fallback.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .store import StoreBackend
from .store_memory import MemoryStoreBackend

logger = logging.getLogger("adapter.store_redis")

_PREFIX = "adapter:"


class RedisStoreBackend(StoreBackend):
    """Redis-backed store with local in-memory cache fallback."""

    def __init__(self, config: Dict[str, Any]) -> None:
        try:
            import redis as redis_lib  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "redis is required for redis backend: pip install redis"
            ) from exc

        url = config.get("url", "redis://localhost:6379/0")
        password = os.getenv("ADAPTER_REDIS_PASSWORD") or None
        self._event_ttl = int(config.get("event_ttl_seconds", 86400))
        self._r = redis_lib.Redis.from_url(url, password=password, decode_responses=True)
        self._inner = MemoryStoreBackend()

        try:
            self._r.ping()
            logger.info("redis connected: %s", url)
        except Exception:
            logger.exception("redis connection failed: %s", url)
            raise

    def _key(self, *parts: str) -> str:
        return _PREFIX + ":".join(parts)

    def _task_key(self, task_id: str) -> str:
        return self._key("task", task_id)

    def _result_key(self, task_id: str) -> str:
        return self._key("result", task_id)

    def _meta_key(self, task_id: str) -> str:
        return self._key("meta", task_id)

    def _events_key(self, task_id: str) -> str:
        return self._key("events", task_id)

    def _history_key(self) -> str:
        return self._key("history")

    def _meta_index_key(self) -> str:
        """ZSET key used as a secondary index for list_meta() — scored by created_at."""
        return self._key("meta", "_index")

    @staticmethod
    def _meta_score(meta: Dict[str, Any]) -> float:
        created_at = meta.get("created_at", datetime.now(timezone.utc).isoformat())
        try:
            return datetime.fromisoformat(str(created_at).replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return datetime.now(timezone.utc).timestamp()

    @staticmethod
    def _load_json_dict(raw: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(raw, str) or not raw.strip():
            return None
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None
        return data if isinstance(data, dict) else None

    def _set_json_dict(self, key: str, payload: Dict[str, Any]) -> None:
        try:
            self._r.set(key, json.dumps(payload, ensure_ascii=False))
        except Exception:
            logger.exception("redis set failed: key=%s", key)

    def _get_json_dict(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            raw = self._r.get(key)
        except Exception:
            logger.exception("redis get failed: key=%s", key)
            return None
        return self._load_json_dict(raw)

    @staticmethod
    def _parse_meta_map(raw: Any) -> Dict[str, Any]:
        if not isinstance(raw, dict):
            return {}
        parsed: Dict[str, Any] = {}
        for key, value in raw.items():
            if not isinstance(key, str):
                continue
            if isinstance(value, str):
                try:
                    parsed[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed[key] = value
            else:
                parsed[key] = value
        return parsed

    # ── Task envelope ──

    def save_task(self, task_id: str, envelope: Dict[str, Any]) -> None:
        self._inner.save_task(task_id, envelope)
        self._set_json_dict(self._task_key(task_id), envelope)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        payload = self._get_json_dict(self._task_key(task_id))
        if payload is not None:
            self._inner.save_task(task_id, payload)
            return payload
        return self._inner.get_task(task_id)

    def has_task(self, task_id: str) -> bool:
        try:
            if bool(self._r.exists(self._task_key(task_id))):
                return True
        except Exception:
            logger.exception("redis exists failed: task_id=%s", task_id)
        return self._inner.has_task(task_id)

    # ── Result envelope ──

    def save_result(self, task_id: str, result: Dict[str, Any]) -> None:
        self._inner.save_result(task_id, result)
        self._set_json_dict(self._result_key(task_id), result)

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        payload = self._get_json_dict(self._result_key(task_id))
        if payload is not None:
            self._inner.save_result(task_id, payload)
            return payload
        return self._inner.get_result(task_id)

    def has_result(self, task_id: str) -> bool:
        try:
            if bool(self._r.exists(self._result_key(task_id))):
                return True
        except Exception:
            logger.exception("redis exists failed: task_id=%s", task_id)
        return self._inner.has_result(task_id)

    # ── Task meta (Redis hash) ──

    def save_meta(self, task_id: str, meta: Dict[str, Any]) -> None:
        self._inner.save_meta(task_id, meta)
        key = self._meta_key(task_id)
        flat = {
            k: json.dumps(v, ensure_ascii=False)
            for k, v in meta.items()
            if v is not None
        }
        if not flat:
            return
        try:
            self._r.hset(key, mapping=flat)
        except Exception:
            logger.exception("redis hset failed: key=%s", key)

        # P2-1: Maintain ZSET secondary index for O(log N) list_meta().
        score = self._meta_score(meta)
        try:
            self._r.zadd(self._meta_index_key(), {task_id: score})
        except Exception:
            logger.exception("redis zadd meta index failed: task_id=%s", task_id)

    def get_meta(self, task_id: str) -> Optional[Dict[str, Any]]:
        key = self._meta_key(task_id)
        try:
            raw = self._r.hgetall(key)
        except Exception:
            logger.exception("redis hgetall failed: key=%s", key)
            raw = {}
        parsed = self._parse_meta_map(raw)
        if parsed:
            if "task_id" not in parsed:
                parsed["task_id"] = task_id
            self._inner.save_meta(task_id, parsed)
            return parsed
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
        def _match(val: Optional[str], target: Optional[str]) -> bool:
            if target is None:
                return True
            return str(val or "").strip() == target.strip()

        # P2-1: Use ZSET secondary index for main path listing.
        task_ids: List[str] = []
        try:
            # ZREVRANGE returns newest first (descending score).
            task_ids = self._r.zrevrange(self._meta_index_key(), 0, -1)
        except Exception:
            logger.exception("redis zrevrange failed for meta index")

        rows: Dict[str, Dict[str, Any]] = {}
        for task_id in task_ids:
            if not isinstance(task_id, str):
                continue
            try:
                raw = self._r.hgetall(self._meta_key(task_id))
            except Exception:
                logger.exception("redis hgetall failed: task_id=%s", task_id)
                continue
            meta = self._parse_meta_map(raw)
            if not meta:
                continue
            if "task_id" not in meta:
                meta["task_id"] = task_id
            rows[task_id] = meta

        # Backward compatibility:
        # Existing deployments may have historical meta hashes without ZSET index.
        # Scan hash keys and backfill index lazily so old records are visible.
        try:
            prefix = self._meta_key("")
            cursor: Any = 0
            while True:
                cursor, batch = self._r.scan(cursor=cursor, match=self._meta_key("*"), count=200)
                for key in batch:
                    if not isinstance(key, str) or not key.startswith(prefix):
                        continue
                    task_id = key[len(prefix) :]
                    if not task_id or task_id == "_index" or task_id in rows:
                        continue
                    try:
                        raw = self._r.hgetall(self._meta_key(task_id))
                    except Exception:
                        logger.exception("redis hgetall failed: task_id=%s", task_id)
                        continue
                    meta = self._parse_meta_map(raw)
                    if not meta:
                        continue
                    if "task_id" not in meta:
                        meta["task_id"] = task_id
                    rows[task_id] = meta
                    try:
                        self._r.zadd(self._meta_index_key(), {task_id: self._meta_score(meta)})
                    except Exception:
                        logger.exception("redis zadd meta index backfill failed: task_id=%s", task_id)
                if cursor in (0, "0"):
                    break
        except Exception:
            logger.exception("redis scan failed for legacy meta backfill")

        if not rows:
            return self._inner.list_meta(
                command=command,
                tenant_id=tenant_id,
                operator_id=operator_id,
                status=status,
                limit=limit,
                offset=offset,
            )

        filtered: List[Dict[str, Any]] = []
        for task_id, meta in rows.items():
            row = dict(meta)
            result = self.get_result(task_id)
            if isinstance(result, dict):
                row["status"] = result.get("status", row.get("status"))
                row["decision"] = result.get("result", {}).get("decision")
                row["summary"] = str(result.get("result", {}).get("summary", ""))[:180]
            if (
                _match(row.get("command"), command)
                and _match(row.get("tenant_id"), tenant_id)
                and _match(row.get("operator_id"), operator_id)
                and _match(row.get("status"), status)
            ):
                filtered.append(row)

        filtered.sort(key=lambda x: self._meta_score(x), reverse=True)
        total = len(filtered)
        items = filtered[offset : offset + limit]
        return {"total": total, "limit": limit, "offset": offset, "items": items}

    # ── Events (Redis sorted set) ──

    def save_event(self, task_id: str, event: Dict[str, Any]) -> None:
        self._inner.save_event(task_id, event)
        key = self._events_key(task_id)
        ts = event.get("timestamp", datetime.now(timezone.utc).isoformat())
        try:
            score = datetime.fromisoformat(ts).timestamp()
        except (ValueError, TypeError):
            score = datetime.now(timezone.utc).timestamp()
        try:
            self._r.zadd(key, {json.dumps(event, ensure_ascii=False): score})
            if self._event_ttl > 0:
                self._r.expire(key, self._event_ttl)
        except Exception:
            logger.exception("redis zadd failed: key=%s", key)

    def list_events(self, task_id: str) -> List[Dict[str, Any]]:
        key = self._events_key(task_id)
        try:
            raw = self._r.zrange(key, 0, -1)
        except Exception:
            logger.exception("redis zrange failed: key=%s", key)
            raw = []
        if raw:
            events = []
            for item in raw:
                try:
                    event = json.loads(item)
                except (json.JSONDecodeError, TypeError):
                    continue
                if isinstance(event, dict):
                    events.append(event)
            if events:
                return events
        return self._inner.list_events(task_id)

    def delete_events(self, task_id: str) -> int:
        count = self._inner.delete_events(task_id)
        key = self._events_key(task_id)
        try:
            redis_count = int(self._r.delete(key))
        except Exception:
            logger.exception("redis delete failed: key=%s", key)
            redis_count = 0
        return max(count, redis_count)

    # ── History logs (Redis list) ──

    def save_history(self, record: Dict[str, Any]) -> None:
        self._inner.save_history(record)
        key = self._history_key()
        try:
            self._r.rpush(key, json.dumps(record, ensure_ascii=False))
        except Exception:
            logger.exception("redis rpush failed: key=%s", key)

    def list_history(
        self, *, task_id: Optional[str] = None, limit: int = 200
    ) -> List[Dict[str, Any]]:
        key = self._history_key()
        try:
            raw = self._r.lrange(key, 0, -1)
        except Exception:
            logger.exception("redis lrange failed: key=%s", key)
            raw = []

        rows: List[Dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, str):
                continue
            try:
                record = json.loads(item)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                rows.append(record)

        if not rows:
            return self._inner.list_history(task_id=task_id, limit=limit)

        if task_id is not None:
            rows = [row for row in rows if row.get("task_id") == task_id]
        return rows[-limit:]

    # ── Cascade delete ──

    def delete_task(self, task_id: str, *, purge_events: bool = True) -> Dict[str, Any]:
        result = self._inner.delete_task(task_id, purge_events=purge_events)

        try:
            self._r.delete(self._task_key(task_id))
            self._r.delete(self._result_key(task_id))
            self._r.delete(self._meta_key(task_id))
            # P2-1: Remove from ZSET secondary index.
            self._r.zrem(self._meta_index_key(), task_id)
            redis_removed_events = int(self._r.delete(self._events_key(task_id))) if purge_events else 0
        except Exception:
            logger.exception("redis delete cascade failed: task_id=%s", task_id)
            redis_removed_events = 0

        result["removed_events"] = int(result.get("removed_events", 0) or 0) + redis_removed_events
        return result

    # ── Lifecycle ──

    def close(self) -> None:
        try:
            self._r.close()
        except Exception:
            pass
