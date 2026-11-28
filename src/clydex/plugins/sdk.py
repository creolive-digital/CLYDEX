"""Plugin SDK v1 wire contracts. No credential or authorization capability."""
from dataclasses import dataclass
from typing import Protocol

from clydex.core.contracts import Cancellation
from clydex.security.schema import object_schema, validate

SDK_VERSION = 1
EVENTS = ('workflow.started', 'workflow.stopped', 'system.sample', 'feed.status')
LOG_CODES = ('started', 'complete', 'cancelled', 'invalid_input', 'unavailable')


@dataclass(frozen=True)
class PluginContext:
    cancel: Cancellation
    configuration: dict

    def log(self, code: str) -> dict:
        if code not in LOG_CODES:
            raise ValueError('Plugin logs contain allowlisted codes only.')
        return {'code': code}


class ToolAdapter(Protocol):
    def invoke(self, name: str, arguments: dict, context: PluginContext) -> dict: ...


class FeedAdapter(Protocol):
    def refresh(self, context: PluginContext) -> dict: ...


class IntegrationAdapter(Protocol):
    def request(self, operation: str, data: dict, context: PluginContext) -> dict: ...


class EventAdapter(Protocol):
    def on_event(self, event: str, metadata: dict, context: PluginContext) -> None: ...


class HealthAdapter(Protocol):
    def health(self, context: PluginContext) -> dict: ...


def validate_response(value, schema):
    validate(value, object_schema(sdk_version={'type': 'integer', 'enum': [1]},
                                result=schema, logs={'type': 'array', 'maxItems': 16,
                                                    'items': {'type': 'string', 'enum': list(LOG_CODES)}}))
    return value['result']


def workflow_node(plugin_id, tool, arguments):
    """SDK nodes invoke the fixed host wrapper and inherit its HIGH risk policy."""
    return {'tool': 'plugins.invoke', 'arguments': {'plugin': plugin_id, 'tool': tool, 'arguments': arguments}}
