"""One provider coordinator for the existing agent; never replays a tool plan."""
import json

from clydex.core.commands import PLAN
from clydex.core.context import ContextBundle
from clydex.core.contracts import ProviderRequest, canonical_json
from clydex.providers.base import ProviderConfig, ProviderFailure
from clydex.providers.codex import validate_response
from clydex.providers.router import ProviderRouter
from clydex.security.outbound import OutboundPolicy


class IntelligenceCoordinator:
    def __init__(self, registry=None, memory=None):
        self.registry, self.memory = registry, memory
        self.state = {'provider': 'codex', 'model': '', 'status': 'idle', 'usage': {}, 'memory_used': 0}

    def respond(self, engine, instructions: str, data: dict, schema: dict):
        memories = self.memory.relevant(str(data.get('request', ''))) if self.memory else []
        context = ContextBundle.from_legacy(data, memories,
            local_only=bool(data.get('history') and getattr(engine, 'history_local_only', False)))
        task = 'planning' if schema is PLAN else 'summary' if 'results' in data else 'conversation'
        size = len((instructions + canonical_json(context.data()) + canonical_json(schema)).encode('utf-8')) + 1024
        registry = self.registry
        if registry is None:
            config = ProviderConfig('codex', enabled=True)
        else:
            config = ProviderRouter(registry).select(context, privacy=engine.config.privacy_mode,
                                                     allow_cloud=engine.config.allow_cloud, task_type=task, size=size)
        tried, attempt = set(), 0
        request_cost_ceiling = config.max_request_cost
        while True:
            engine.cancel_token.check()
            actual = context.for_provider(config.capabilities.local)
            routing = registry.routing if registry else None
            cost = OutboundPolicy.check(config, actual,
                privacy=engine.config.privacy_mode or bool(routing and routing.privacy),
                offline=bool(routing and (routing.offline or routing.profile == 'offline')),
                allow_cloud=engine.config.allow_cloud, task_type=task, size=size)
            arguments = dict(instructions=instructions, data=actual.data(), schema=schema, fast=schema is PLAN,
                             configuration=canonical_json(dict(config.public_dict(), original_request_cost_ceiling=request_cost_ceiling)),
                             attempt=attempt)
            self.state = dict(provider=config.id, model=config.model, status='requesting', usage={},
                              memory_used=len(json.loads(actual.memory_json)), estimated_ceiling=cost)
            engine.events.put(('provider_state', dict(self.state)))
            provider = registry.build(config) if registry else engine.provider

            def complete(a):
                # Execute the immutable approved snapshot, not mutable UI configuration.
                request = ProviderRequest(a['instructions'], canonical_json(a['data']),
                                          canonical_json(a['schema']), timeout=config.timeout, fast=a['fast'])
                if config.id == 'codex':
                    value = provider.respond(request, engine.cancel_token)
                else:
                    received = 0
                    def progress(text):
                        nonlocal received
                        received += len(text)
                        engine.events.put(('provider_delta', {'received_characters': received}))
                    value = provider.respond(request, engine.cancel_token,
                                             on_delta=progress)
                validate_response(value, a['schema'])
                return value
            try:
                value = engine.execute_tool('provider.' + config.id,
                    f'{config.id} / {config.model or "CLI default"} / {config.endpoint or "Codex CLI"}',
                    arguments, complete,
                    'Send the displayed context to this provider? Local-only memories are omitted from cloud requests.',
                    explicit_cloud_request=(config.id == 'codex' and not actual.private and attempt == 0))
                if config.capabilities.local and any(m.get('local_only', True) for m in json.loads(actual.memory_json)):
                    engine.history_local_only = True
                    engine.turn_sensitive = True
                if actual.local_only:
                    engine.turn_sensitive = True
                usage = getattr(provider, 'last_usage', {})
                self.state.update(status='complete', usage=usage if isinstance(usage, dict) else {})
                engine.last_provider, engine.last_model = config.id, config.model
                engine.events.put(('provider_state', dict(self.state)))
                return value
            except ProviderFailure as exc:
                self.state['status'] = exc.kind
                engine.events.put(('provider_state', dict(self.state)))
                if registry:
                    registry.health[config.id] = exc.kind
                # Only an explicit 429 rejection can be retried, with fresh review.
                # Timeouts/network failures might already have incurred cost.
                if exc.kind == 'rate_limit' and attempt < config.retries:
                    attempt += 1
                    continue
                tried.add(config.id)
                fallbacks = tuple(name for name in registry.routing.fallbacks if name not in tried) if registry else ()
                if not fallbacks or exc.kind in ('authentication', 'invalid_request', 'invalid_response'):
                    raise
                config = ProviderRouter(registry).select(actual, privacy=engine.config.privacy_mode,
                    allow_cloud=engine.config.allow_cloud, task_type=task, size=size, candidates=fallbacks,
                    request_cost_ceiling=request_cost_ceiling)
                attempt += 1  # Every fallback gets its own exact-action consent.

    def check_provider(self, engine, name: str) -> str:
        if self.registry is None or name not in self.registry.configs:
            raise ValueError('Unknown provider.')
        config = self.registry.configs[name]
        routing = self.registry.routing
        OutboundPolicy.check(config, ContextBundle(''), privacy=engine.config.privacy_mode or routing.privacy,
                             offline=routing.offline or routing.profile == 'offline',
                             allow_cloud=engine.config.allow_cloud, task_type='conversation', size=0)
        return engine.execute_tool('provider.health', name,
            {'configuration': canonical_json(config.public_dict())},
            lambda _: self.registry.check(config, engine.cancel_token),
            'Check this configured endpoint/model? No conversation or memory content will be sent.')
