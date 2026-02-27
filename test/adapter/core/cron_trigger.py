"""Cron trigger — periodic system health checks and stale task recovery.

Uses threading.Timer for zero-dependency scheduling. Submits /heartbeat
TaskEnvelopes to the adapter API and logs diagnostic results.
"""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("adapter.cron_trigger")

# Default timeout for stale task detection (seconds).
_DEFAULT_STALE_TIMEOUT = 600


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
        stale_timeout_sec: int = _DEFAULT_STALE_TIMEOUT,
    ) -> None:
        self._interval = max(interval_seconds, 10)
        self._tenant_id = tenant_id
        self._operator_id = operator_id
        self._stale_timeout = max(stale_timeout_sec, 60)
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
        # P2-2: Recover stale tasks after heartbeat.
        try:
            self._recover_stale_tasks()
        except Exception:
            logger.exception("stale task recovery failed")
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

    def _recover_stale_tasks(self) -> None:
        """P2-2: Detect and recover tasks stuck in 'processing' beyond stale_timeout."""
        from .state import get_state
        from .types import ResultEnvelope

        state = get_state()
        now = datetime.now(timezone.utc)
        recovered = 0

        with state.lock:
            meta_list = state.store.list_meta(status="processing", limit=200)

        items = meta_list.get("items", [])
        if not items:
            return

        for item in items:
            task_id = item.get("task_id", "")
            if not task_id:
                continue

            created_at_raw = item.get("created_at", "")
            if not created_at_raw:
                continue

            try:
                created_text = str(created_at_raw).replace("Z", "+00:00")
                created_at = datetime.fromisoformat(created_text)
                # Make offset-naive for comparison if needed.
                if created_at.tzinfo is None:
                    elapsed = (now.replace(tzinfo=None) - created_at).total_seconds()
                else:
                    elapsed = (now - created_at).total_seconds()
            except (ValueError, TypeError):
                continue

            if elapsed < self._stale_timeout:
                continue

            # Mark as timed out.
            timeout_envelope = ResultEnvelope(
                task_id=task_id,
                command=item.get("command", "/unknown"),
                status="timeout",
                result={
                    "decision": "needs_review",
                    "confidence": 0.0,
                    "summary": f"task timed out after {int(elapsed)}s (limit: {self._stale_timeout}s)",
                    "issues": [
                        {
                            "severity": "error",
                            "category": "timeout",
                            "description": f"task exceeded stale timeout ({self._stale_timeout}s)",
                            "evidence_ref": "cron://stale-recovery",
                        }
                    ],
                    "evidence": [
                        {
                            "id": "cron-stale-001",
                            "type": "system",
                            "source": "adapter/core/cron_trigger.py",
                            "content": f"recovered stale task after {int(elapsed)}s",
                        }
                    ],
                },
                execution={
                    "model_used": "none",
                    "agents_invoked": [],
                    "parallel_tasks": 0,
                    "tools_called": [],
                },
                error={
                    "code": "ADAPTER_TASK_TIMEOUT",
                    "message": f"task exceeded stale timeout ({self._stale_timeout}s)",
                    "recoverable": True,
                },
            )

            with state.lock:
                state.store.save_result(task_id, asdict(timeout_envelope))
                state.events.emit(task_id, "stale_recovery", {
                    "elapsed_seconds": int(elapsed),
                    "timeout_limit": self._stale_timeout,
                })

            recovered += 1
            logger.warning(
                "recovered stale task: task_id=%s elapsed=%ds",
                task_id, int(elapsed),
            )

        if recovered:
            logger.info("stale task recovery: recovered %d task(s)", recovered)

