"""SDK integration exports."""

from .bridge import execute_task

# Backward-compatible alias for legacy imports.
execute_task_sdk = execute_task

__all__ = ["execute_task", "execute_task_sdk"]
