"""Adaptive RMS capture gate; Faster Whisper also applies its local Silero VAD.

This is noise-aware energy detection, not speaker authentication or echo removal.
"""
import math


class SilenceDetector:
    def __init__(self, config, frame_ms: int = 20):
        self.config, self.frame_ms = config, frame_ms
        self.noise = config.noise_floor / config.noise_ratio
        self.elapsed_ms = self.speech_ms = self.silence_ms = 0
        self.started = False

    def accept(self, rms: float) -> bool:
        if not math.isfinite(rms) or rms < 0:
            raise ValueError('Invalid audio level.')
        self.elapsed_ms += self.frame_ms
        speech = rms >= max(self.config.noise_floor, self.noise * self.config.noise_ratio)
        if speech:
            self.speech_ms += self.frame_ms
            self.silence_ms = 0
            self.started = self.speech_ms >= self.config.min_speech_ms
        else:
            self.noise = .98 * self.noise + .02 * min(rms, self.config.noise_floor)
            if self.started:
                self.silence_ms += self.frame_ms
            else:
                self.speech_ms = 0
        return self.finished

    @property
    def finished(self) -> bool:
        return (self.elapsed_ms >= self.config.max_recording_seconds * 1000
                or (self.started and self.silence_ms >= self.config.silence_ms)
                or (not self.started and self.elapsed_ms >= self.config.initial_silence_seconds * 1000))
