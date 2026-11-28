"""Mocked local model protocol; no model download or neural accuracy claim."""
from dataclasses import replace
import json
import unittest
import httpx
from clydex_cloud.core.errors import CloudError
from clydex_cloud.knowledge.embeddings import LocalEmbeddings
import test_security


class EmbeddingTests(unittest.TestCase):
    def setUp(self):
        test_security.SecurityTests.setUp(self)
        self.model = replace(self.settings, embedding_model='fixture-local:1', embedding_revision='synthetic-digest',
            embedding_dimensions=2, embedding_license='Synthetic fixture; no model asset', local_embeddings_confirmed=True)

    def test_only_installed_exact_digest_and_bounded_untruncated_local_embedding(self):
        requests = []
        def respond(request):
            requests.append(request)
            if request.url.path == '/api/tags':
                return httpx.Response(200, json={'models':[{'name':'fixture-local:1','digest':'synthetic-digest'}]})
            self.assertFalse(json.loads(request.content)['truncate'])
            return httpx.Response(200, json={'embeddings':[[1., 0.]]})
        model = LocalEmbeddings(self.model, transport=httpx.MockTransport(respond))
        self.assertEqual(model.embed(['Synthetic evidence']), [[1., 0.]])
        self.assertEqual([r.url.path for r in requests], ['/api/tags','/api/embed'])
        self.assertTrue(all(r.url.host == '127.0.0.1' for r in requests))

    def test_missing_revision_remote_failure_and_nonfinite_vectors_fail_closed(self):
        def wrong_revision(request):
            return httpx.Response(200, json={'models':[{'name':'fixture-local:1','digest':'different'}]})
        with self.assertRaises(CloudError) as mismatch:
            LocalEmbeddings(self.model, transport=httpx.MockTransport(wrong_revision)).embed(['fixture'])
        self.assertEqual(mismatch.exception.code, 'embedding_model_revision_mismatch')
        def timeout(request):
            raise httpx.ReadTimeout('Never expose a synthetic private query')
        with self.assertRaises(CloudError) as failed:
            LocalEmbeddings(self.model, transport=httpx.MockTransport(timeout)).embed(['fixture'])
        self.assertEqual(failed.exception.code, 'embedding_service_unavailable')
        def zero(request):
            return httpx.Response(200, json={'models':[{'name':'fixture-local:1','digest':'synthetic-digest'}]}) if request.url.path == '/api/tags' else httpx.Response(200, json={'embeddings':[[0,0]]})
        with self.assertRaises(CloudError) as invalid:
            LocalEmbeddings(self.model, transport=httpx.MockTransport(zero)).embed(['fixture'])
        self.assertEqual(invalid.exception.code, 'embedding_response_invalid')
