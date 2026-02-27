"""Cron trigger — periodic system health checks.

Uses threading.Timer for zero-dependency scheduling. Submits /heartbeat
TaskEnvelopes to the adapter API and logs diagnostic results.
"""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("adapter.cron_trigger")


class CronTrigger:
    """Background scheduler that periodically runs system health checks.

    Usage::

        trigger = CronTrigger(interval_seconds=60)
        trigger.start()
        # ...
        trigger.stop()
    """

    def __init__(
        self,
        interval_seconds: int = 60,
        tenant_id: str = "system",
        operator_id: str = "cron",
    ) -> None:
        self._interval = max(interval_seconds, 10)
        self._tenant_id = tenant_id
        self._operator_id = operator_id
        self._timer: Optional[threading.Timer] = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._schedule_next()
        logger.info("cron trigger started (interval=%ds)", self._interval)

    def stop(self) -> None:
        self._running = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        logger.info("cron trigger stopped")

    def _schedule_next(self) -> None:
        if not self._running:
            return
        self._timer = threading.Timer(self._interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        if not self._running:
            return
        try:
            self._run_heartbeat()
        except Exception:
            logger.exception("heartbeat tick failed")
        finally:
            self._schedule_next()

    def _run_heartbeat(self) -> None:
        """Execute a system health check and log results."""
        from .history import write_history_record
        from .state import get_state

        task_id = f"heartbeat-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        # Collect diagnostics
        diagnostics = self._collect_diagnostics()

        # Record heartbeat directly in history (bypass validator — /heartbeat is internal)
        record_payload = {
            "check_time": now,
            "diagnostics": diagnostics,
            "tenant_id": self._tenant_id,
            "operator_id": self._operator_id,
        }
        write_history_record("heartbeat", task_id, record_payload)

        # Also persist to store as an event for observability
        try:
            state = get_state()
            with state.lock:
                state.events.emit(task_id, "heartbeat", record_payload)
        except Exception:
            pass

        logger.info(
            "heartbeat completed: task_id=%s diagnostics=%s",
            task_id, diagnostics,
        )

    def _collect_diagnostics(self) -> Dict[str, Any]:
        """Collect system health metrics."""
        try:
            from .usecases.runtime import queue_runtime

            runtime = queue_runtime()
            diagnostics: Dict[str, Any] = {
                "queue_healthy": True,
                "running_sessions": len(runtime.get("running_sessions", [])),
                "running_tasks": len(runtime.get("running_tasks", [])),
                "pending_count": runtime.get("pending_count", 0),
                "max_concurrent": runtime.get("max_concurrent_sessions", 0),
            }

            # Stale task detection: flag if pending > 2x max_concurrent
            max_c = runtime.get("max_concurrent_sessions", 4)
            pending = runtime.get("pending_count", 0)
            if pending > max_c * 2:
                diagnostics["queue_healthy"] = False
                diagnostics["warning"] = f"pending tasks ({pending}) exceed 2x max_concurrent ({max_c})"

            return diagnostics
        except Exception as exc:
            return {"queue_healthy": False, "error": str(exc)}
