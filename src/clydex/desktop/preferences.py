"""Validated non-secret presentation preferences; no capture/AI authority."""
from dataclasses import asdict, dataclass, replace
import re

from clydex.core.settings import read_settings, write_settings


@dataclass(frozen=True)
class PresentationPreferences:
    theme: str = 'cyber'
    accent: str = '#00d9ff'
    reduced_motion: bool = False
    animations: bool = True
    resource_saving: bool = False
    fps: int = 30
    particles: int = 180
    detail: str = 'balanced'
    startup_animation: bool = True
    startup_sound: bool = False
    startup_greeting: bool = False
    sounds_muted: bool = True
    sound_volume: int = 25
    dnd: bool = False
    native_notifications: bool = False

    def __post_init__(self):
        if self.theme not in ('cyber', 'midnight', 'graphite') or self.detail not in ('low', 'balanced', 'high'):
            raise ValueError('Unsupported presentation preset.')
        if not isinstance(self.accent, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', self.accent):
            raise ValueError('Use an RGB accent color.')
        for name in ('reduced_motion', 'animations', 'resource_saving', 'startup_animation',
                     'startup_sound', 'startup_greeting', 'sounds_muted', 'dnd', 'native_notifications'):
            if type(getattr(self, name)) is not bool:
                raise ValueError('Presentation flags must be booleans.')
        if type(self.fps) is not int or self.fps not in (15, 30, 60):
            raise ValueError('Select 15, 30 or 60 FPS.')
        if type(self.particles) is not int or not 0 <= self.particles <= 500:
            raise ValueError('Particle count outside supported limits.')
        if type(self.sound_volume) is not int or not 0 <= self.sound_volume <= 100:
            raise ValueError('Invalid sound volume.')


class DesktopPreferences:
    def __init__(self, paths):
        self.path = paths.directory('settings') / 'desktop.json'
        self.values = PresentationPreferences(**read_settings(self.path))

    def configure(self, changes: dict) -> dict:
        values = replace(self.values, **changes)
        write_settings(self.path, asdict(values))
        self.values = values
        return asdict(values)
