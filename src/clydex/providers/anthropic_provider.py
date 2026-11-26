"""Anthropic Messages API with output_config JSON Schema and SSE."""
from clydex.providers.http_provider import HTTPProvider


class AnthropicProvider(HTTPProvider):
    protocol = 'anthropic'
