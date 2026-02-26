"""In-memory store backend — default for dev and tests.

Preserves the original Dict-based behavior from api_server.py.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Optional

from .store import StoreBackend


class MemoryStoreBackend(StoreBackend):
    """Thread-safe in-memory store. Caller must hold the external lock."""

    def __init__(self, *, max_events_per_task: int = 200) -> None:
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        self._meta: Dict[str, Dict[str, Any]] = {}
        self._events: Dict[str, Deque[Dict[str, Any]]] = defaultdict(deque)
        self._history: List[Dict[str, Any]] = []
        self._max_events = max_events_per_task

    # ── Task envelope ──

    def save_task(self, task_id: str, envelope: Dict[str, Any]) -> None:
        self._tasks[task_id] = dict(envelope)

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        data = self._tasks.get(task_id)
        return dict(data) if data is not None else None

    def has_task(self, task_id: str) -> bool:
        return task_id in self._tasks

    # ── Result envelope ──

    def save_result(self, task_id: str, result: Dict[str, Any]) -> None:
        self._results[task_id] = dict(result)

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        data = self._results.get(task_id)
        return dict(data) if data is not None else None

    def has_result(self, task_id: str) -> bool:
        return task_id in self._results

    # ── Task meta ──

    def save_meta(self, task_id: str, meta: Dict[str, Any]) -> None:
        self._meta[task_id] = dict(meta)

    def get_meta(self, task_id: str) -> Optional[Dict[str, Any]]:
        data = self._meta.get(task_id)
        return dict(data) if data is not None else None

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

        rows = []
        for task_id, meta in self._meta.items():
            row = dict(meta)
            result = self._results.get(task_id)
            if result is not None:
                row["status"] = result.get("status", row.get("status"))
                row["decision"] = result.get("result", {}).get("decision")
                row["summary"] = str(result.get("result", {}).get("summary", ""))[:180]
            if (
                _match(row.get("command"), command)
                and _match(row.get("tenant_id"), tenant_id)
                and _match(row.get("operator_id"), operator_id)
                and _match(row.get("status"), status)
            ):
                rows.append(row)

        rows.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        total = len(rows)
        items = rows[offset : offset + limit]
        return {"total": total, "limit": limit, "offset": offset, "items": items}

    # ── Events ──

    def save_event(self, task_id: str, event: Dict[str, Any]) -> None:
        bucket = self._events[task_id]
        bucket.append(dict(event))
        while len(bucket) > self._max_events:
            bucket.popleft()

    def list_events(self, task_id: str) -> List[Dict[str, Any]]:
        return list(self._events.get(task_id, []))

    def delete_events(self, task_id: str) -> int:
        bucket = self._events.pop(task_id, None)
        return len(bucket) if bucket else 0

    # ── History logs ──

    def save_history(self, record: Dict[str, Any]) -> None:
        self._history.append(dict(record))

    def list_history(
        self, *, task_id: Optional[str] = None, limit: int = 200
    ) -> List[Dict[str, Any]]:
        if task_id is not None:
            filtered = [r for r in self._history if r.get("task_id") == task_id]
        else:
            filtered = list(self._history)
        return filtered[-limit:]

    # ── Cascade delete ──

    def delete_task(self, task_id: str) -> Dict[str, bool]:
        had_task = self._tasks.pop(task_id, None) is not None
        had_result = self._results.pop(task_id, None) is not None
        had_meta = self._meta.pop(task_id, None) is not None
        events_bucket = self._events.pop(task_id, None)
        removed_events = len(events_bucket) if events_bucket else 0
        return {
            "removed_task": had_task,
            "removed_result": had_result,
            "removed_meta": had_meta,
            "removed_events": removed_events,
        }
