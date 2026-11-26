"""Gemini generateContent / streamGenerateContent JSON-schema codec."""
from clydex.providers.http_provider import HTTPProvider


class GeminiProvider(HTTPProvider):
    protocol = 'gemini'
