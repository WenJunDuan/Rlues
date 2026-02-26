"""Runtime diagnostics use cases."""

from __future__ import annotations

from typing import Any, Dict

from ..state import get_state


def queue_runtime() -> Dict[str, Any]:
    """Expose queue and worker runtime status for diagnostics."""
    state = get_state()
    with state.lock:
        return {
            "status": "ok",
            "max_concurrent_sessions": state.queue.max_concurrent,
            "running_sessions": sorted(list(state.queue.running_sessions)),
            "running_tasks": sorted(list(state.running_tasks)),
            "pending_sessions": state.queue.pending_session_keys(),
            "pending_count": state.queue.total_pending(),
            "worker_count": len(state.running_tasks),
        }
