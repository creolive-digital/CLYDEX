"""Bounded transient status notifications, never private prompt/tool content."""
import threading
import time
import uuid

MESSAGES = {
    'resource.alert': 'A configured local resource threshold was exceeded. Review Monitoring.',
    'task.complete': 'Local task completed.', 'task.interrupted': 'Task interrupted. Completed effects remain.',
    'approval.waiting': 'An action needs your review.', 'voice.warning': 'Local voice needs attention. Check Voice settings.',
    'task.error': 'A task could not complete. Check the conversation and settings.',
    'timer.alert': 'A timer or alarm needs attention.',
}


class NotificationCenter:
    def __init__(self):
        self._items = []
        self._lock = threading.Lock()

    def add(self, code: str) -> dict:
        if code not in MESSAGES:
            raise ValueError('Only trusted generic notification codes are allowed.')
        with self._lock:
            item = dict(id=uuid.uuid4().hex, code=code, message=MESSAGES[code], timestamp=time.time())
            self._items = (self._items + [item])[-100:]
            return dict(item)

    def snapshot(self) -> list[dict]:
        with self._lock:
            return [dict(item) for item in self._items]

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
