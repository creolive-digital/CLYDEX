"""Owner-configured HTTPS OpenAI Chat Completions compatible endpoint."""
from clydex.providers.http_provider import HTTPProvider


class CustomProvider(HTTPProvider):
    protocol = 'chat'
