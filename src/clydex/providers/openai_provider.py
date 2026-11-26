"""OpenAI Responses API codec; model/account must be configured explicitly."""
from clydex.providers.http_provider import HTTPProvider


class OpenAIProvider(HTTPProvider):
    protocol = 'openai'
