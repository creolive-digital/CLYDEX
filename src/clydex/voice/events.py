"""Transport-independent voice states/events and optional real engine timing."""
from dataclasses import dataclass
from enum import Enum
import time
from typing import Any, Callable


class VoiceState(str, Enum):
    STANDBY = 'standby'
    WAKE_DETECTED = 'wake_detected'
    LISTENING = 'listening'
    TRANSCRIBING = 'transcribing'
    THINKING = 'thinking'
    WAITING_FOR_APPROVAL = 'waiting_for_approval'
    SPEAKING = 'speaking'
    INTERRUPTED = 'interrupted'
    SLEEPING = 'sleeping'
    ERROR = 'error'


@dataclass(frozen=True)
class SpeechTiming:
    offset_seconds: float
    duration_seconds: float
    phoneme: str | None = None
    viseme: str | None = None


@dataclass(frozen=True)
class VoiceEvent:
    kind: str
    state: str
    timestamp: float
    details: dict[str, Any]


class VoiceEvents:
    def __init__(self, sink: Callable[[tuple], None], clock=time.monotonic):
        self.sink, self.clock = sink, clock
        self._last_audio = 0.

    def emit(self, kind: str, state: VoiceState = VoiceState.STANDBY, **details) -> None:
        # Never include transcript/audio bytes in diagnostic or progress metadata.
        self.sink(('voice_event', dict(kind=kind, state=state.value, timestamp=self.clock(), details=details)))

    def audio(self, spectrum, direction: str) -> None:
        now = self.clock()
        if now - self._last_audio < .1:
            return
        self._last_audio = now
        level, bands, _ = spectrum.read_display()
        self.sink(('voice_telemetry', dict(kind='audio', direction=direction, timestamp=now,
                                         amplitude=level, frequency_spectrum=bands)))
