"""Installed providers and validated, non-secret per-user settings; no auto-connect."""
from dataclasses import asdict, dataclass, replace
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading

from clydex.providers.anthropic_provider import AnthropicProvider
from clydex.providers.base import PROVIDER_IDS, ProviderConfig, ProviderFailure
from clydex.providers.codex import CodexProvider
from clydex.providers.custom_provider import CustomProvider
from clydex.providers.gemini_provider import GeminiProvider
from clydex.providers.ollama_provider import OllamaProvider
from clydex.providers.openai_provider import OpenAIProvider
from clydex.providers.openrouter_provider import OpenRouterProvider


@dataclass(frozen=True)
class RoutingConfig:
    selected: str = 'codex'
    automatic: bool = False
    profile: str = 'balanced'
    offline: bool = False
    privacy: bool = False
    fast: tuple[str, ...] = ('codex',)
    balanced: tuple[str, ...] = ('codex',)
    advanced: tuple[str, ...] = ('codex',)
    offline_order: tuple[str, ...] = ('ollama',)
    fallbacks: tuple[str, ...] = ()

    def __post_init__(self):
        if self.selected not in PROVIDER_IDS or self.profile not in ('fast', 'balanced', 'advanced', 'offline'):
            raise ValueError('Invalid routing selection.')
        if any(type(v) is not bool for v in (self.automatic, self.offline, self.privacy)):
            raise ValueError('Invalid routing flag.')
        for name in ('fast', 'balanced', 'advanced', 'offline_order', 'fallbacks'):
            values = getattr(self, name)
            if not isinstance(values, (list, tuple)) or len(values) > 7 or any(v not in PROVIDER_IDS for v in values):
                raise ValueError('Invalid routing order.')
            object.__setattr__(self, name, tuple(dict.fromkeys(values)))


class ProviderRegistry:
    classes = {'openai': OpenAIProvider, 'anthropic': AnthropicProvider, 'gemini': GeminiProvider,
               'ollama': OllamaProvider, 'openrouter': OpenRouterProvider, 'custom': CustomProvider}

    def __init__(self, paths, credentials, transport=None):
        self.paths, self.credentials, self.transport = paths, credentials, transport
        self._lock = threading.RLock()
        self.configs = {name: ProviderConfig(name, enabled=name == 'codex') for name in PROVIDER_IDS}
        self.routing = RoutingConfig()
        self.health: dict[str, str] = {}
        path = self._path
        if path.exists():
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or set(data) - {'providers', 'routing'}:
                raise ValueError('Invalid provider settings document.')
            for name, value in data.get('providers', {}).items():
                if name not in PROVIDER_IDS or value.get('id', name) != name:
                    raise ValueError('Invalid provider configuration.')
                self.configs[name] = ProviderConfig(**dict(value, id=name))
            self.routing = RoutingConfig(**data.get('routing', {}))

    @property
    def _path(self) -> Path:
        return self.paths.directory('settings') / 'providers.json'

    def _save(self, configs: dict, routing: RoutingConfig) -> None:
        data = {'providers': {key: value.public_dict() for key, value in configs.items()},
                'routing': asdict(routing)}
        temporary = None
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=self._path.parent, delete=False) as file:
                temporary = Path(file.name)
                json.dump(data, file, ensure_ascii=False, allow_nan=False, indent=2)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self._path)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()

    def configure(self, name: str, values: dict, secret: str | None = None, remove_key: bool = False):
        with self._lock:
            if name not in self.configs or not isinstance(values, dict) or 'id' in values:
                raise ValueError('Invalid provider configuration.')
            config = replace(self.configs[name], **values)
            if secret is not None and (not isinstance(secret, str) or not secret or len(secret) > 1280
                                       or not secret.isascii() or any(c.isspace() for c in secret)):
                raise ValueError('Credential must be an ASCII token without whitespace.')
            if secret is not None and remove_key:
                raise ValueError('Choose replace or remove credential.')
            # Keys are never part of the serializable configuration.
            if secret is not None:
                if not config.requires_key:
                    raise ValueError('This provider does not use an API key.')
                self.credentials.set('provider.' + name, secret)
            if remove_key:
                self.credentials.delete('provider.' + name)
            updated = dict(self.configs, **{name: config})
            self._save(updated, self.routing)
            self.configs = updated
            self.health.pop(name, None)

    def configure_routing(self, values: dict):
        with self._lock:
            routing = replace(self.routing, **values)
            self._save(self.configs, routing)
            self.routing = routing

    def build(self, config: ProviderConfig):
        if config.id == 'codex':
            return CodexProvider(self.paths.directory('tmp'), config=config)
        return self.classes[config.id](config, self.credentials, self.transport)

    def ready(self, config: ProviderConfig) -> bool:
        if not config.enabled:
            return False
        if config.requires_key:
            try:
                return bool(self.credentials.get('provider.' + config.id))
            except Exception:
                return False
        return True

    def snapshot(self) -> dict:
        with self._lock:
            providers = []
            for name, config in self.configs.items():
                status = ('disabled' if not config.enabled else
                          'unconfigured' if not self.ready(config) else self.health.get(name, 'unchecked'))
                providers.append(dict(config.public_dict(), status=status, requires_key=config.requires_key,
                                      capabilities=asdict(config.capabilities)))
            return {'providers': providers, 'routing': asdict(self.routing)}

    def check(self, config: ProviderConfig, cancel) -> str:
        if not self.ready(config):
            raise ProviderFailure('configuration')
        if config.id == 'codex':
            status = 'cli_installed_login_unverified' if (shutil.which('codex') or shutil.which('codex.cmd')) else 'missing'
        else:
            try:
                status = self.build(config).check(cancel)
            except ProviderFailure as exc:
                self.health[config.id] = exc.kind
                raise
        self.health[config.id] = status
        return status
