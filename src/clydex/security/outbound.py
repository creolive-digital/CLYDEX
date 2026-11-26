"""Shared trusted policy for every provider and each retry/fallback."""
from clydex.core.context import ContextBundle
from clydex.core.errors import PermissionDenied
from clydex.providers.base import ProviderConfig


class OutboundPolicy:
    @staticmethod
    def check(provider: ProviderConfig, context: ContextBundle, *, privacy: bool,
              offline: bool, allow_cloud: bool, task_type: str, size: int) -> float | None:
        if not provider.enabled or task_type not in provider.capabilities.task_types:
            raise PermissionDenied('Provider is disabled or lacks the required capability.')
        if size > provider.max_request_bytes:
            raise PermissionDenied('Context exceeds the configured provider limit.')
        if provider.capabilities.local:
            if not provider.local_only_confirmed:
                raise PermissionDenied('Confirm local-only Ollama deployment before sending context.')
        elif privacy or offline or context.local_only or not allow_cloud:
            raise PermissionDenied('Local-only policy prevents this outbound request.')
        if provider.id not in ('codex', 'ollama') and not provider.allow_paid:
            raise PermissionDenied('Paid/custom endpoint use has not been explicitly allowed.')
        estimated = provider.estimate_cost(provider.max_request_bytes)
        if provider.max_request_cost is not None and (
                estimated is None or estimated > provider.max_request_cost):
            raise PermissionDenied('Configured cost ceiling cannot be met or verified.')
        return estimated
