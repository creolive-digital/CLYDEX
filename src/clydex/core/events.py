"""Bounded thread-safe events; tuple compatibility for the existing Studio UI."""
from dataclasses import dataclass
import queue
import threading
from typing import Any


@dataclass(frozen=True)
class CoreEvent:
    kind: str
    value: Any = None


class EventChannel:
    """Discard oldest telemetry first; never block an audio callback or grow without bound.

    Conversation history lives in the engine; this channel is a transient UI feed.
    A slow/disconnected consumer can lose old messages and must refresh state.
    """

    def __init__(self, capacity: int = 256):
        if type(capacity) is not int or capacity < 8:
            raise ValueError('Event capacity must be at least eight.')
        self.capacity = capacity
        self._items: list[CoreEvent] = []
        self._lock = threading.Lock()
        self.dropped = 0

    def put(self, event: CoreEvent | tuple) -> None:
        event = event if isinstance(event, CoreEvent) else CoreEvent(*event)
        with self._lock:
            if event.kind in ('status', 'audio_stream', 'provider_state', 'provider_delta', 'voice_telemetry'):
                self._items = [e for e in self._items if e.kind != event.kind]
            if len(self._items) >= self.capacity:
                index = next((i for i, e in enumerate(self._items)
                              if e.kind in ('status', 'audio_stream', 'provider_state', 'provider_delta', 'voice_telemetry')), 0)
                self._items.pop(index)
                self.dropped += 1
            self._items.append(event)

    def get_nowait(self) -> tuple:
        with self._lock:
            if not self._items:
                raise queue.Empty
            event = self._items.pop(0)
            return event.kind, event.value

    def qsize(self) -> int:
        with self._lock:
            return len(self._items)
