"""Headless typed boundaries; adapters import native/audio dependencies lazily."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Iterable, Protocol
from threading import Event

from clydex.core.contracts import Cancellation
from clydex.voice.config import VoiceConfig


@dataclass(frozen=True)
class AudioBuffer:
    samples: AnySamples
    sample_rate: int


class AnySamples(Protocol):
    def __len__(self) -> int: ...


@dataclass(frozen=True)
class PCMChunk:
    data: bytes
    sample_rate: int
    channels: int = 1
    sample_width: int = 2


@dataclass(frozen=True)
class Transcript:
    text: str
    language: str | None
    minimum_logprob: float
    language_probability: float | None = None


class AudioInput(Protocol):
    def capture(self, config: VoiceConfig, cancel: Cancellation, finish: Event, guard: Callable[[], None],
                *, check_only: bool = False, listen_seconds: float | None = None) -> AudioBuffer: ...

    def wake_frames(self, config: VoiceConfig, cancel: Cancellation, guard: Callable[[], None],
                    accept: Callable[[AnySamples, Cancellation], bool]) -> bool: ...


class SpeechRecognizer(Protocol):
    def recognize(self, audio: AudioBuffer, config: VoiceConfig, cancel: Cancellation,
                  guard: Callable[[], None]) -> Transcript: ...
    def wait_closed(self) -> None: ...


class SpeechSynthesizer(Protocol):
    def synthesize(self, text: str, config: VoiceConfig, cancel: Cancellation,
                   guard: Callable) -> Iterable[PCMChunk]: ...


class AudioOutput(Protocol):
    def play(self, chunks: Iterable[PCMChunk], config: VoiceConfig, cancel: Cancellation, guard: Callable) -> None: ...


class WakeDetector(Protocol):
    def accept(self, pcm16: AnySamples, cancel: Cancellation) -> bool: ...
    def reset(self) -> None: ...


class ActivityDetector(Protocol):
    started: bool

    def accept(self, rms: float) -> bool: ...
    @property
    def finished(self) -> bool: ...


class ConversationLifecycle(Protocol):
    def run(self, config: VoiceConfig, cancel: Cancellation, finish: Event, guard: Callable[[], None],
            dispatch: Callable[[str], None], *, check_only: bool = False, wake: bool = False) -> None: ...


class InterruptibleVoice(Protocol):
    def mute(self) -> None: ...
    def stop(self) -> None: ...
    def close(self) -> None: ...
    def wait_closed(self) -> None: ...
