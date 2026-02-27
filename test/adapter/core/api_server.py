"""Framework-agnostic API layer facade.

This module keeps backward-compatible exports while delegating business logic to
`core.usecases` modules.
"""

from __future__ import annotations

from .history import archive_logs, list_logs
from .scheduler import bootstrap_runtime
from .usecases.history import delete_history, list_history
from .usecases.query import get_compliance_feedback, get_result, get_task_meta, stream_events
from .usecases.runtime import queue_runtime
from .usecases.submit import submit_task


def bootstrap_on_import() -> None:
    """Explicitly bootstrap the runtime. Called by gateway create_app()."""
    bootstrap_runtime()


__all__ = [
    "submit_task",
    "get_task_meta",
    "get_result",
    "get_compliance_feedback",
    "stream_events",
    "list_history",
    "delete_history",
    "list_logs",
    "archive_logs",
    "queue_runtime",
    "bootstrap_on_import",
]
