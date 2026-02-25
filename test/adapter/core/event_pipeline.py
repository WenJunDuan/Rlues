"""In-memory event pipeline for task event buffering."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, Dict, List


@dataclass
class EventPipeline:
    max_events_per_task: int = 200
    events: Dict[str, Deque[dict]] = field(default_factory=lambda: defaultdict(deque))

    def emit(self, task_id: str, event_type: str, data: dict) -> None:
        bucket = self.events[task_id]
        bucket.append(
            {
                "task_id": task_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                "data": data,
            }
        )
        while len(bucket) > self.max_events_per_task:
            bucket.popleft()

    def list_events(self, task_id: str) -> List[dict]:
        return list(self.events.get(task_id, []))

    def remove_task(self, task_id: str) -> int:
        bucket = self.events.pop(task_id, None)
        return len(bucket) if bucket else 0
