"""Abstract store backend interface for adapter persistence.

Provides a pluggable persistence layer. Concrete implementations:
- MemoryStoreBackend (store_memory.py) — default, for dev/tests
- RedisStoreBackend  (store_redis.py)  — event/meta cache
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StoreBackend(ABC):
    """Protocol for pluggable persistence."""

    # ── Task envelope ──

    @abstractmethod
    def save_task(self, task_id: str, envelope: Dict[str, Any]) -> None: ...

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def has_task(self, task_id: str) -> bool: ...

    # ── Result envelope ──

    @abstractmethod
    def save_result(self, task_id: str, result: Dict[str, Any]) -> None: ...

    @abstractmethod
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def has_result(self, task_id: str) -> bool: ...

    # ── Task meta ──

    @abstractmethod
    def save_meta(self, task_id: str, meta: Dict[str, Any]) -> None: ...

    @abstractmethod
    def get_meta(self, task_id: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def list_meta(
        self,
        *,
        command: Optional[str] = None,
        tenant_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]: ...

    # ── Events ──

    @abstractmethod
    def save_event(self, task_id: str, event: Dict[str, Any]) -> None: ...

    @abstractmethod
    def list_events(self, task_id: str) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def delete_events(self, task_id: str) -> int: ...

    # ── History logs ──

    @abstractmethod
    def save_history(self, record: Dict[str, Any]) -> None: ...

    @abstractmethod
    def list_history(
        self, *, task_id: Optional[str] = None, limit: int = 200
    ) -> List[Dict[str, Any]]: ...

    # ── Cascade delete ──

    @abstractmethod
    def delete_task(self, task_id: str, *, purge_events: bool = True) -> Dict[str, Any]:
        """Delete all data for a task. Returns what was removed."""
        ...

    # ── Lifecycle ──

    def close(self) -> None:
        """Release resources (connections, pools)."""


def create_store(backend_type: str, config: Dict[str, Any]) -> StoreBackend:
    """Factory: create a store backend by type name."""
    if backend_type == "memory":
        from .store_memory import MemoryStoreBackend

        return MemoryStoreBackend()

    if backend_type == "redis":
        from .store_redis import RedisStoreBackend

        return RedisStoreBackend(config.get("redis", {}))

    raise ValueError(f"unknown store backend: {backend_type!r} (supported: memory, redis)")
