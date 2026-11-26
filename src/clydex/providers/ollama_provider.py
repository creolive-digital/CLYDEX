"""Explicit local-only Ollama chat adapter; no model download or cloud routing."""
from clydex.providers.http_provider import HTTPProvider


class OllamaProvider(HTTPProvider):
    protocol = 'ollama'
