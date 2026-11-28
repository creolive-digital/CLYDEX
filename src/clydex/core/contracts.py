"""Transport-independent immutable request and execution contracts."""
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Callable, Protocol
import uuid


def canonical_json(value: Any) -> str:
    """Reject non-JSON values/NaN; detach input objects before review or execution."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


class Risk(str, Enum):
    LOW = 'low'
    SENSITIVE = 'sensitive'
    HIGH = 'high'


@dataclass(frozen=True)
class RequestContext:
    user_id: str
    device_id: str
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    source: str = 'user'

    def __post_init__(self) -> None:
        if any(not isinstance(v, str) or not v.strip() or len(v) > 256
               for v in (self.user_id, self.device_id, self.request_id)):
            raise ValueError('Request identity is required.')
        if self.source not in ('user', 'model', 'workflow', 'plugin', 'device'):
            raise ValueError('Invalid request source.')


@dataclass(frozen=True)
class ActionRequest:
    tool: str
    target: str
    arguments_json: str
    context: RequestContext

    @classmethod
    def create(cls, tool: str, target: str, arguments: dict, context: RequestContext) -> 'ActionRequest':
        if not isinstance(tool, str) or not tool or not isinstance(target, str):
            raise ValueError('Invalid action target or tool.')
        if not isinstance(arguments, dict):
            raise ValueError('Tool arguments must be an object.')
        encoded = canonical_json(arguments)
        if len(encoded.encode('utf-8')) > 262144:
            raise ValueError('Tool request is too large.')
        return cls(tool, target, encoded, context)

    @property
    def arguments(self) -> dict:
        return json.loads(self.arguments_json)

    @property
    def digest(self) -> str:
        payload = dict(tool=self.tool, target=self.target, arguments=self.arguments,
                       user=self.context.user_id, device=self.context.device_id,
                       request=self.context.request_id, source=self.context.source)
        return hashlib.sha256(canonical_json(payload).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class ToolSpec:
    name: str
    scope: str
    risk: Risk
    timeout: float
    fields: tuple[tuple[str, type], ...]
    result_types: tuple[type, ...]
    description: str = ''
    argument_schema_json: str = ''
    result_schema_json: str = ''
    platforms: tuple[str, ...] = ('Windows', 'Linux', 'Darwin')
    read_only: bool = False
    destinations: tuple[str, ...] = ()
    idempotent: bool = False
    approval_required: bool = True
    cancellation: str = 'cooperative; completed effects cannot be undone'
    audit_metadata: tuple[str, ...] = ('action_digest', 'tool', 'outcome')

    def validate(self, arguments: dict) -> None:
        expected = dict(self.fields)
        if set(arguments) != set(expected):
            raise ValueError('Unexpected or missing tool arguments.')
        if any(type(arguments[key]) is not kind for key, kind in expected.items()):
            raise ValueError('Invalid tool argument type.')
        if self.argument_schema_json:
            from clydex.security.schema import validate
            validate(arguments, json.loads(self.argument_schema_json))

    def validate_result(self, result) -> None:
        if type(result) not in self.result_types:
            raise ValueError('Tool result type mismatch.')
        if self.result_schema_json:
            from clydex.security.schema import validate
            validate(result, json.loads(self.result_schema_json))

    def inventory(self) -> dict:
        kinds = {str: 'string', dict: 'object', list: 'array', int: 'integer', bool: 'boolean', type(None): 'null', float: 'number'}
        schema = json.loads(self.argument_schema_json) if self.argument_schema_json else {
            'type': 'object', 'properties': {k: {'type': kinds[t]} for k, t in self.fields},
            'required': [k for k, _ in self.fields], 'additionalProperties': False}
        result_schema = json.loads(self.result_schema_json) if self.result_schema_json else {
            'oneOf': [{'type': kinds.get(t, 'object')} for t in self.result_types]}
        return dict(id=self.name, description=self.description or self.name.replace('.', ' '), scope=self.scope,
                    risk=self.risk.value, timeout=self.timeout, arguments=schema,
                    results=result_schema,
                    platforms=list(self.platforms), read_only=self.read_only,
                    destinations=list(self.destinations), idempotent=self.idempotent,
                    approval_required=self.approval_required, cancellation=self.cancellation,
                    approval_policy='One-time exact review; legacy LOW user actions and explicit context-free Codex requests retain documented exceptions',
                    audit_metadata=list(self.audit_metadata))


@dataclass(frozen=True)
class ProviderRequest:
    instructions: str
    data_json: str
    schema_json: str
    timeout: float = 180
    fast: bool = False


class Cancellation(Protocol):
    def is_set(self) -> bool: ...


class AIProvider(Protocol):
    name: str

    def respond(self, request: ProviderRequest, cancel: Cancellation) -> dict: ...


ToolOperation = Callable[[dict], Any]
