"""Event pipeline with pluggable sinks.

In-memory buffer (primary) + optional external sinks (Langfuse, notification).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger("adapter.event_pipeline")


class EventSink(ABC):
    """Protocol for external event sinks."""

    @abstractmethod
    def emit(self, task_id: str, event_type: str, data: Dict[str, Any]) -> None: ...


class LangfuseSink(EventSink):
    """Forward events to Langfuse for observability.

    Requires LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and optionally
    LANGFUSE_HOST env vars to be set.
    """

    def __init__(self) -> None:
        self._client: Any = None
        try:
            from langfuse import Langfuse  # type: ignore

            self._client = Langfuse()
            logger.info("langfuse sink initialized")
        except ImportError:
            logger.warning("langfuse not installed; LangfuseSink disabled")
        except Exception:
            logger.exception("langfuse init failed; LangfuseSink disabled")

    def emit(self, task_id: str, event_type: str, data: Dict[str, Any]) -> None:
        if self._client is None:
            return
        try:
            self._client.event(
                name=event_type,
                metadata={"task_id": task_id, **data},
            )
        except Exception:
            logger.exception("langfuse emit failed: task=%s type=%s", task_id, event_type)


class NotificationSink(EventSink):
    """Forward warning/error events to a notification gateway URL.

    Configure via ADAPTER_NOTIFICATION_URL env var.
    """

    SEVERITY_TYPES = {"error", "warning", "task_failed"}

    def __init__(self, url: Optional[str] = None) -> None:
        import os

        self._url = url or os.getenv("ADAPTER_NOTIFICATION_URL", "")
        if self._url:
            logger.info("notification sink configured: %s", self._url)

    def emit(self, task_id: str, event_type: str, data: Dict[str, Any]) -> None:
        if not self._url:
            return
        if event_type not in self.SEVERITY_TYPES:
            return
        try:
            import urllib.request
            import json

            payload = json.dumps(
                {"task_id": task_id, "event_type": event_type, "data": data},
                ensure_ascii=False,
            ).encode("utf-8")
            req = urllib.request.Request(
                self._url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            logger.exception("notification emit failed: task=%s type=%s", task_id, event_type)


class EventPipeline:
    """In-memory event buffer with pluggable external sinks."""

    def __init__(self, max_events_per_task: int = 200) -> None:
        self._events: Dict[str, Deque[Dict[str, Any]]] = defaultdict(deque)
        self._max = max_events_per_task
        self._sinks: List[EventSink] = []

    def add_sink(self, sink: EventSink) -> None:
        """Register an external event sink."""
        self._sinks.append(sink)

    def emit(self, task_id: str, event_type: str, data: Dict[str, Any]) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        event = {"task_id": task_id, "type": event_type, "data": data, "timestamp": timestamp}

        # Primary in-memory buffer
        bucket = self._events[task_id]
        bucket.append(event)
        while len(bucket) > self._max:
            bucket.popleft()

        # Forward to external sinks (best-effort)
        for sink in self._sinks:
            try:
                sink.emit(task_id, event_type, data)
            except Exception:
                logger.exception("sink emit failed: %s", type(sink).__name__)

    def list_events(self, task_id: str) -> List[Dict[str, Any]]:
        return list(self._events.get(task_id, []))

    def remove_task(self, task_id: str) -> int:
        bucket = self._events.pop(task_id, None)
        return len(bucket) if bucket else 0
