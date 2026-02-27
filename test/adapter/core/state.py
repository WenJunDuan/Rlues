"""Centralized runtime state for adapter.

Holds all shared state (store backend, queue, events, locks) in one place.
Replaces the module-level globals previously scattered across api_server.py.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional, Set

from .config import DEFAULT_CONFIG
from .event_pipeline import EventPipeline
from .persistence_config import PERSISTENCE_CONFIG
from .store import StoreBackend, create_store
from .task_queue import TaskQueue


class AdapterState:
    """Singleton-ish state container for the adapter runtime."""

    def __init__(self) -> None:
        self.store: StoreBackend = create_store(
            PERSISTENCE_CONFIG.backend,
            PERSISTENCE_CONFIG.to_dict(),
        )
        self.queue = TaskQueue(max_concurrent=DEFAULT_CONFIG.max_concurrent_sessions)
        self.events = EventPipeline(max_events_per_task=DEFAULT_CONFIG.max_events_per_task)
        self.running_tasks: Set[str] = set()
        self.lock = threading.RLock()

    def close(self) -> None:
        self.store.close()


# Module-level singleton — created on first import.
_state: Optional[AdapterState] = None
_init_lock = threading.Lock()


def get_state() -> AdapterState:
    """Get or create the global AdapterState singleton.

    Falls back to memory store if the configured backend fails to initialize.
    """
    global _state
    if _state is not None:
        return _state
    with _init_lock:
        if _state is not None:
            return _state
        try:
            _state = AdapterState()
        except Exception as exc:
            import logging
            logging.getLogger("adapter.core.state").warning(
                "State init failed (%s), falling back to MemoryStoreBackend", exc,
            )
            from .store_memory import MemoryStoreBackend
            fallback = AdapterState.__new__(AdapterState)
            fallback.store = MemoryStoreBackend()
            fallback.queue = TaskQueue(max_concurrent=DEFAULT_CONFIG.max_concurrent_sessions)
            fallback.events = EventPipeline(max_events_per_task=DEFAULT_CONFIG.max_events_per_task)
            fallback.running_tasks = set()
            fallback.lock = threading.RLock()
            _state = fallback
        return _state


def reset_state() -> None:
    """Reset global state — only for tests."""
    global _state
    with _init_lock:
        if _state is not None:
            _state.close()
        _state = None
