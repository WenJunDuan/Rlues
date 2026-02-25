"""SDK integration layer for Claude runtime calls."""

from .bridge import execute_task, execute_task_sdk

__all__ = ["execute_task", "execute_task_sdk"]
