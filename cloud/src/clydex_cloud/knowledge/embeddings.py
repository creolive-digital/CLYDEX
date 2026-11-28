"""Optional owner-configured local Ollama embeddings, never pulls a model."""
import math
import httpx

from clydex_cloud.core.errors import CloudError


class LocalEmbeddings:
    def __init__(self, settings, *, transport=None):
        self.settings, self.transport = settings, transport

    @property
    def configured(self) -> bool:
        return bool(self.settings.embedding_model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            return self._embed(texts)
        except CloudError:
            raise
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            raise CloudError('embedding_service_unavailable', 503) from None

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if not self.configured or not self.settings.local_embeddings_confirmed:
            raise CloudError('embedding_model_unconfigured', 409)
        if not 1 <= len(texts) <= 32 or any(len(t) > 2000 for t in texts):
            raise CloudError('embedding_input_limit', 422)
        with httpx.Client(base_url='http://127.0.0.1:11434', timeout=20, trust_env=False,
                          follow_redirects=False, transport=self.transport) as client:
            with client.stream('GET', '/api/tags') as response:
                content = self._bounded(response)
            models = content.get('models', [])
            selected = next((m for m in models if m.get('name') == self.settings.embedding_model), None)
            if not selected or selected.get('digest') != self.settings.embedding_revision:
                raise CloudError('embedding_model_revision_mismatch', 409)
            with client.stream('POST', '/api/embed', json=dict(model=self.settings.embedding_model,
                    input=texts, truncate=False)) as response:
                result = self._bounded(response)
        vectors = result.get('embeddings')
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise CloudError('embedding_response_invalid', 502)
        for vector in vectors:
            if (not isinstance(vector, list) or len(vector) != self.settings.embedding_dimensions
                    or any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 3.4e38 for v in vector)
                    or not sum(v * v for v in vector) > 0):
                raise CloudError('embedding_response_invalid', 502)
        return vectors

    @staticmethod
    def _bounded(response):
        import json
        if response.status_code != 200:
            raise CloudError('embedding_service_unavailable', 503)
        result = bytearray()
        for chunk in response.iter_bytes():
            result.extend(chunk)
            if len(result) > 2 * 1024**2:
                raise CloudError('embedding_response_limit', 502)
        value = json.loads(result)
        if not isinstance(value, dict):
            raise CloudError('embedding_response_invalid', 502)
        return value
