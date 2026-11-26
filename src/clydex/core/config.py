"""Validated non-secret configuration and per-user runtime directory ownership."""
from dataclasses import dataclass, fields
import json
import os
from pathlib import Path
from typing import Mapping

from clydex.security.permissions import TOOL_SPECS


@dataclass(frozen=True)
class RuntimePaths:
    root: Path

    @classmethod
    def for_user(cls) -> 'RuntimePaths':
        local = os.environ.get('LOCALAPPDATA')
        if not local or not Path(local).is_absolute():
            raise ValueError('An absolute LOCALAPPDATA directory is required on Windows.')
        return cls(Path(local) / 'CLYDEX')

    def directory(self, name: str) -> Path:
        if name not in ('data', 'memory', 'cache', 'models', 'logs', 'backups',
                        'settings', 'plugins', 'tmp'):
            raise ValueError('Unknown runtime directory.')
        return self.root / name

    def ensure(self) -> None:
        if not self.root.is_absolute():
            raise ValueError('Runtime root must be absolute.')
        # Do not allow an environment override to put private runtime files in source.
        source = Path(__file__).resolve().parents[3]
        for candidate in (source, Path.cwd().resolve()):
            if (candidate / 'pyproject.toml').exists() and (
                    self.root.resolve() == candidate or candidate in self.root.resolve().parents):
                raise ValueError('Runtime storage cannot be inside the source repository.')
        for name in ('data', 'memory', 'cache', 'models', 'logs', 'backups',
                     'settings', 'plugins', 'tmp'):
            self.directory(name).mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class AppConfig:
    recognition_mode: str = 'en'
    speak_replies: bool = True
    allow_cloud: bool = True
    privacy_mode: bool = False
    approval_timeout: int = 120
    event_capacity: int = 256
    disabled_scopes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.recognition_mode not in ('en', 'en-accurate', 'auto'):
            raise ValueError('Unsupported recognition mode.')
        if any(type(v) is not bool for v in (self.speak_replies, self.allow_cloud, self.privacy_mode)):
            raise ValueError('Configuration flags must be booleans.')
        if type(self.approval_timeout) is not int or not 5 <= self.approval_timeout <= 900:
            raise ValueError('Approval timeout must be between 5 and 900 seconds.')
        if type(self.event_capacity) is not int or not 8 <= self.event_capacity <= 4096:
            raise ValueError('Invalid event capacity.')
        known_scopes = {spec.scope for spec in TOOL_SPECS}
        if (not isinstance(self.disabled_scopes, (list, tuple))
                or any(not isinstance(scope, str) or scope not in known_scopes for scope in self.disabled_scopes)):
            raise ValueError('Unknown disabled permission scope.')
        object.__setattr__(self, 'disabled_scopes', tuple(self.disabled_scopes))

    @classmethod
    def load(cls, paths: RuntimePaths, environ: Mapping[str, str] | None = None) -> 'AppConfig':
        env = os.environ if environ is None else environ
        file = paths.directory('settings') / 'config.json'
        values = json.loads(file.read_text(encoding='utf-8')) if file.exists() else {}
        allowed = {f.name for f in fields(cls)}
        if not isinstance(values, dict) or set(values) - allowed:
            raise ValueError('Unknown configuration fields; secrets do not belong in config.')
        for name in ('allow_cloud', 'privacy_mode'):
            raw = env.get('CLYDEX_' + name.upper())
            if raw is not None:
                if raw.lower() not in ('true', 'false'):
                    raise ValueError('Environment flags must be true or false.')
                values[name] = raw.lower() == 'true'
        if 'CLYDEX_APPROVAL_TIMEOUT' in env:
            values['approval_timeout'] = int(env['CLYDEX_APPROVAL_TIMEOUT'])
        return cls(**values)
