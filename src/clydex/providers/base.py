"""Provider configuration/capabilities. No credentials or invented model defaults."""
from dataclasses import asdict, dataclass
import math
import re
from urllib.parse import urlsplit

from clydex.core.errors import ProviderError
from clydex.security.content import validate_private_text


PROVIDER_IDS = ('codex', 'openai', 'anthropic', 'gemini', 'ollama', 'openrouter', 'custom')
ENDPOINTS = {'codex': '', 'openai': 'https://api.openai.com/v1',
             'anthropic': 'https://api.anthropic.com/v1',
             'gemini': 'https://generativelanguage.googleapis.com/v1beta',
             'ollama': 'http://127.0.0.1:11434', 'openrouter': 'https://openrouter.ai/api/v1', 'custom': ''}


class ProviderFailure(ProviderError):
    """Only normalized codes/status escape a transport, never response bodies/keys."""
    def __init__(self, kind: str, status: int | None = None):
        super().__init__('Provider request failed: ' + kind)
        self.kind, self.status = kind, status


@dataclass(frozen=True)
class ProviderCapabilities:
    structured: bool = True
    streaming: bool = True
    local: bool = False
    task_types: tuple[str, ...] = ('conversation', 'planning', 'summary')


@dataclass(frozen=True)
class ProviderConfig:
    id: str
    enabled: bool = False
    model: str = ''
    endpoint: str = ''
    allow_paid: bool = False
    stream: bool = False
    timeout: int = 180
    max_request_bytes: int = 131072
    max_response_bytes: int = 262144
    max_output_tokens: int = 2048
    retries: int = 0
    max_request_cost: float | None = None
    input_price_per_million: float | None = None
    output_price_per_million: float | None = None
    local_only_confirmed: bool = False
    upstream: str = ''
    api_version: str = '2026-10-21'
    workspace_id: str = ''
    token_parameter: str = 'max_tokens'
    task_types: tuple[str, ...] = ('conversation', 'planning', 'summary')

    def __post_init__(self) -> None:
        if self.id not in PROVIDER_IDS:
            raise ValueError('Unknown provider.')
        if self.id == 'codex' and self.stream:
            raise ValueError('The Codex CLI adapter does not expose streaming.')
        for flag in (self.enabled, self.allow_paid, self.stream, self.local_only_confirmed):
            if type(flag) is not bool:
                raise ValueError('Provider flags must be booleans.')
        for value, lower, upper in ((self.timeout, 1, 900), (self.max_request_bytes, 1024, 262144),
                                     (self.max_response_bytes, 1024, 1048576),
                                     (self.max_output_tokens, 1, 32768), (self.retries, 0, 1)):
            if type(value) is not int or not lower <= value <= upper:
                raise ValueError('Provider limit is outside the supported range.')
        for value in (self.max_request_cost, self.input_price_per_million, self.output_price_per_million):
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                raise ValueError('Costs must be finite non-negative configured values.')
        if (not isinstance(self.model, str) or len(self.model) > 200
                or (self.model and not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_./:+-]*', self.model))):
            raise ValueError('Invalid model identifier.')
        if not isinstance(self.endpoint, str):
            raise ValueError('Invalid endpoint.')
        if self.model:
            validate_private_text(self.model, 200)
        if self.endpoint:
            validate_private_text(self.endpoint, 2000)
        endpoint = self.endpoint.rstrip('/') or ENDPOINTS[self.id]
        object.__setattr__(self, 'endpoint', endpoint)
        if self.id not in ('ollama', 'custom') and endpoint != ENDPOINTS[self.id]:
            raise ValueError('Use the custom provider for a different service endpoint.')
        if endpoint:
            parts = urlsplit(endpoint)
            if (not parts.hostname or parts.username is not None or parts.password is not None
                    or parts.query or parts.fragment or any(c.isspace() for c in endpoint)):
                raise ValueError('Endpoint must not contain credentials, queries or fragments.')
            if self.id == 'ollama':
                if parts.hostname not in ('127.0.0.1', '::1') or parts.scheme not in ('http', 'https'):
                    raise ValueError('Ollama must use a literal loopback endpoint.')
            elif parts.scheme != 'https':
                raise ValueError('Remote endpoints require HTTPS.')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', self.api_version):
            raise ValueError('Invalid API version.')
        if not isinstance(self.workspace_id, str) or (self.workspace_id and not re.fullmatch(r'wrkspc_[a-zA-Z0-9]{1,100}', self.workspace_id)):
            raise ValueError('Invalid Claude workspace identifier.')
        if self.token_parameter not in ('max_tokens', 'max_completion_tokens'):
            raise ValueError('Invalid token limit parameter.')
        if (not isinstance(self.task_types, (tuple, list)) or not self.task_types
                or any(t not in ('conversation', 'planning', 'summary') for t in self.task_types)):
            raise ValueError('Invalid task capabilities.')
        object.__setattr__(self, 'task_types', tuple(self.task_types))
        if not isinstance(self.upstream, str) or (self.upstream and not re.fullmatch(r'[\w./-]{1,120}', self.upstream)):
            raise ValueError('Invalid upstream identifier.')
        if self.enabled and self.id != 'codex' and (not self.model or not endpoint):
            raise ValueError('An enabled HTTP provider needs an explicit model and endpoint.')
        if self.enabled and self.id == 'openrouter' and not self.upstream:
            raise ValueError('Select one approved OpenRouter upstream before enabling.')
        if self.id == 'ollama' and 'cloud' in self.model.casefold():
            raise ValueError('Cloud-routed Ollama models are not supported by the local adapter.')

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(streaming=self.id != 'codex', local=self.id == 'ollama',
                                    task_types=self.task_types)

    @property
    def requires_key(self) -> bool:
        return self.id not in ('codex', 'ollama')

    def public_dict(self) -> dict:
        return asdict(self)

    def estimate_cost(self, request_bytes: int) -> float | None:
        if self.input_price_per_million is None or self.output_price_per_million is None:
            return None
        # UTF-8 bytes conservatively bound input tokens; billing remains provider-specific.
        return (request_bytes * self.input_price_per_million
                + self.max_output_tokens * self.output_price_per_million) / 1_000_000
