"""Validated local voice policy. No background capture, downloads or model by default."""
from dataclasses import asdict, dataclass, replace
import math
from pathlib import PurePosixPath
import re

from clydex.core.settings import read_settings, write_settings


def language_code(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'auto|[a-z]{2,3}(?:-[A-Z]{2})?|singlish', value):
        raise ValueError('Invalid language code.')
    return value


def model_relative(value: str) -> str:
    if (not isinstance(value, str) or len(value) > 200 or '\\' in value or ':' in value
            or PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts):
        raise ValueError('Model artifacts must use relative paths inside the runtime models directory.')
    return value


@dataclass(frozen=True)
class VoiceConfig:
    microphone_enabled: bool = False
    background_listening: bool = False
    continuous: bool = False
    wake_enabled: bool = False
    hotkey_enabled: bool = False
    tray_enabled: bool = False
    mode: str = 'en'
    recognition_language: str = 'en'
    fast_model: str = 'base'
    accurate_model: str = 'small.en'
    input_device: int | None = None
    output_device: int | None = None
    max_recording_seconds: int = 30
    initial_silence_seconds: int = 5
    silence_ms: int = 850
    min_speech_ms: int = 240
    followup_seconds: int = 6
    inactivity_seconds: int = 60
    playback_cooldown_ms: int = 600
    noise_floor: float = .003
    noise_ratio: float = 3.0
    min_avg_logprob: float = -1.0
    max_no_speech: float = .65
    min_language_probability: float = .5
    tts_provider: str = 'sapi'
    voice_id: str = ''
    tts_language: str = 'auto'
    tts_fallback: str = 'none'
    speech_rate: int = 0
    volume: int = 80
    piper_manifest: str = ''
    piper_manifest_digest: str = ''
    wake_manifest: str = ''
    wake_manifest_digest: str = ''
    wake_threshold: float = .8
    hotkey: str = 'CTRL+ALT+SPACE'

    def __post_init__(self):
        for flag in (self.microphone_enabled, self.background_listening, self.continuous, self.wake_enabled,
                     self.hotkey_enabled, self.tray_enabled):
            if type(flag) is not bool:
                raise ValueError('Voice policy flags must be booleans.')
        for device in (self.input_device, self.output_device):
            if device is not None and (type(device) is not int or not 0 <= device <= 65535):
                raise ValueError('Invalid audio device.')
        if self.mode not in ('en', 'en-accurate', 'auto'):
            raise ValueError('Invalid recognition mode.')
        for value in (self.fast_model, self.accurate_model):
            if value not in ('tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en', 'medium', 'medium.en',
                             'large-v1', 'large-v2', 'large-v3', 'large-v3-turbo', 'turbo'):
                raise ValueError('Select a supported local Whisper model name.')
        language_code(self.recognition_language)
        language_code(self.tts_language)
        if self.recognition_language == 'singlish':
            raise ValueError('Singlish is mixed speech; choose automatic, English or Sinhala recognition.')
        for value, lower, upper in ((self.max_recording_seconds, 1, 60), (self.initial_silence_seconds, 1, 30),
                (self.silence_ms, 200, 5000), (self.min_speech_ms, 80, 2000), (self.followup_seconds, 1, 30),
                (self.inactivity_seconds, 5, 600), (self.speech_rate, -10, 10), (self.volume, 0, 100)):
            if type(value) is not int or not lower <= value <= upper:
                raise ValueError('Voice setting outside supported limits.')
        if type(self.playback_cooldown_ms) is not int or not 100 <= self.playback_cooldown_ms <= 3000:
            raise ValueError('Invalid half-duplex playback cooldown.')
        for value, lower, upper in ((self.noise_floor, .00001, .1), (self.noise_ratio, 1.2, 10),
                (self.min_avg_logprob, -2, -.1), (self.max_no_speech, .1, 1),
                (self.min_language_probability, 0, 1), (self.wake_threshold, .01, 1)):
            if type(value) not in (int, float) or not math.isfinite(value) or not lower <= value <= upper:
                raise ValueError('Invalid voice confidence or level setting.')
        if self.tts_provider not in ('sapi', 'piper') or self.tts_fallback not in ('none', 'en'):
            raise ValueError('Select a supported local synthesis provider/fallback.')
        if not isinstance(self.voice_id, str) or len(self.voice_id) > 500 or any(c in self.voice_id for c in '\r\n\0'):
            raise ValueError('Invalid installed voice identifier.')
        for value in (self.piper_manifest, self.wake_manifest):
            model_relative(value)
        for value in (self.piper_manifest_digest, self.wake_manifest_digest):
            if not isinstance(value, str) or (value and not re.fullmatch('[0-9a-f]{64}', value)):
                raise ValueError('Invalid approved artifact manifest digest.')
        if not isinstance(self.hotkey, str) or not re.fullmatch(r'(?:(?:CTRL|ALT|SHIFT|WIN)\+){1,4}(?:[A-Z0-9]|F(?:[1-9]|1[0-9]|2[0-4])|SPACE)', self.hotkey):
            raise ValueError('Use modifiers and one key, such as CTRL+ALT+SPACE.')

    @property
    def language(self) -> str | None:
        return None if self.mode == 'auto' or self.recognition_language == 'auto' else self.recognition_language.split('-')[0]

    @property
    def model(self) -> str:
        name = self.accurate_model if self.mode == 'en-accurate' else self.fast_model
        # An English-only preset must never be presented as multilingual.
        return name.removesuffix('.en') if self.language != 'en' else name


class VoiceSettings:
    def __init__(self, paths=None):
        self.paths = paths
        self.path = paths.directory('settings') / 'voice.json' if paths else None
        self.config = VoiceConfig(**read_settings(self.path)) if self.path else VoiceConfig()

    def configure(self, values: dict) -> VoiceConfig:
        config = replace(self.config, **values)
        if self.path:
            write_settings(self.path, asdict(config))
        self.config = config
        return config
