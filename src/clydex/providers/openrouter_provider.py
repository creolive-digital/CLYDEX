"""OpenRouter chat codec; exactly one owner-approved upstream, no server fallback."""
from clydex.providers.http_provider import HTTPProvider


class OpenRouterProvider(HTTPProvider):
    protocol = 'chat'
