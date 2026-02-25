"""Lane queue implementation for minimal runnable chain.

Rule:
- same session_key serial
- cross session parallel capability is represented by scheduler selection
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional


SessionKey = str


@dataclass
class QueueItem:
    task_id: str
    session_key: SessionKey


@dataclass
class TaskQueue:
    max_concurrent: int = 3
    lanes: Dict[SessionKey, Deque[QueueItem]] = field(default_factory=dict)
    running_sessions: set[SessionKey] = field(default_factory=set)

    def build_session_key(self, tenant_id: str, operator_id: str) -> SessionKey:
        return f"{tenant_id}:{operator_id}"

    def enqueue(self, item: QueueItem) -> int:
        lane = self.lanes.setdefault(item.session_key, deque())
        lane.append(item)
        return len(lane)

    def has_pending(self, session_key: SessionKey) -> bool:
        lane = self.lanes.get(session_key)
        return bool(lane)

    def dequeue_next(self, session_key: SessionKey) -> Optional[QueueItem]:
        lane = self.lanes.get(session_key)
        if not lane:
            return None
        item = lane.popleft()
        if not lane:
            self.lanes.pop(session_key, None)
        return item

    def can_start_session(self, session_key: SessionKey) -> bool:
        if session_key in self.running_sessions:
            return False
        return len(self.running_sessions) < self.max_concurrent

    def mark_session_start(self, session_key: SessionKey) -> None:
        self.running_sessions.add(session_key)

    def mark_session_done(self, session_key: SessionKey) -> None:
        self.running_sessions.discard(session_key)

    def pending_session_keys(self) -> List[SessionKey]:
        return [key for key, lane in self.lanes.items() if lane]

    def lane_size(self, session_key: SessionKey) -> int:
        lane = self.lanes.get(session_key)
        return len(lane) if lane else 0

    def total_pending(self) -> int:
        return sum(len(lane) for lane in self.lanes.values())

    def remove_task(self, task_id: str) -> bool:
        removed = False
        for session_key, lane in list(self.lanes.items()):
            kept = deque(item for item in lane if item.task_id != task_id)
            if len(kept) != len(lane):
                removed = True
                if kept:
                    self.lanes[session_key] = kept
                else:
                    self.lanes.pop(session_key, None)
        return removed
