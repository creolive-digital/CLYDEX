"""Deterministic routing over explicitly configured capabilities and constraints."""
from clydex.core.errors import PermissionDenied
from clydex.security.outbound import OutboundPolicy


class ProviderRouter:
    def __init__(self, registry):
        self.registry = registry

    def select(self, context, *, privacy: bool, allow_cloud: bool, task_type: str, size: int,
               candidates: tuple[str, ...] | None = None):
        routing = self.registry.routing
        offline = routing.offline or routing.profile == 'offline'
        if candidates is None:
            if offline:
                candidates = routing.offline_order
            elif routing.automatic:
                candidates = getattr(routing, routing.profile)
            else:
                candidates = (routing.selected,)
        for name in candidates:
            config = self.registry.configs[name]
            if not self.registry.ready(config):
                continue
            if self.registry.health.get(name) in ('network', 'timeout', 'authentication', 'model_unavailable', 'missing'):
                continue
            try:
                OutboundPolicy.check(config, context.for_provider(config.capabilities.local),
                                     privacy=privacy or routing.privacy,
                                     offline=offline, allow_cloud=allow_cloud, task_type=task_type, size=size)
            except PermissionDenied:
                continue
            return config
        raise PermissionDenied('No enabled provider satisfies model, context, health, privacy and cost constraints.')
