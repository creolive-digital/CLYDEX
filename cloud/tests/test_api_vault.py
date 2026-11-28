"""Actual FastAPI paths with synthetic SQL simulation and owned parser processes."""
from dataclasses import replace
import unittest
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from clydex_cloud.api.app import create_app
from clydex_cloud.core.runtime import Runtime
from clydex_cloud.repositories.schema import versions
import test_security


class ApiVaultTests(unittest.TestCase):
    def setUp(self):
        test_security.SecurityTests.setUp(self)
        self.runtime = Runtime(self.settings, database=self.db, cipher=self.cipher)
        self.app = create_app(self.settings, runtime=self.runtime)
        self.client = TestClient(self.app, base_url='http://localhost')
        self.headers = {'Authorization': 'Bearer ' + self.tokens['access_token']}

    def collection(self):
        response = self.client.post('/v1/collections', json={'title': 'Synthetic collection', 'description': ''}, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['id']

    def upload(self, collection, name='source.md', content=b'The synthetic launch codeword is CYAN. Known document fact.'):
        response = self.client.post(f'/v1/collections/{collection}/documents', params={'name': name}, content=content,
            headers={**self.headers, 'Idempotency-Key': str(uuid.uuid4()), 'Content-Type': 'application/octet-stream'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_authentication_validation_and_privacy_safe_errors(self):
        self.assertEqual(self.client.get('/v1/collections').status_code, 401)
        response = self.client.post('/v1/auth/login', json={'login': 'synthetic-owner', 'password': 'Synthetic-Login-Fixture-83', 'unexpected': 'SYNTHETIC-NOT-FOR-ERROR-OUTPUT'})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('SYNTHETIC-NOT-FOR-ERROR-OUTPUT', response.text)
        self.assertNotIn('Synthetic-Login-Fixture-83', response.text)
        self.assertEqual(self.client.post('/v1/auth/register', json={'login': 'new-fixture',
            'password': 'New-Fixture-Password-83', 'invitation': 'x' * 48}).status_code, 403)
        self.assertEqual(self.client.get('/readyz').json(), {'status': 'ready'})
        self.assertNotIn('shell', ' '.join(self.app.openapi()['paths']))

    def test_actual_parser_ingestion_keyword_citation_and_encrypted_files(self):
        collection = self.collection()
        uploaded = self.upload(collection)
        self.assertTrue(self.runtime.worker.tick())
        listed = self.client.get('/v1/documents', headers=self.headers).json()['items'][0]
        self.assertEqual(listed['status'], 'ready')
        response = self.client.post('/v1/knowledge/search', json={'query': 'CYAN', 'mode': 'keyword', 'limit': 5}, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        citation = response.json()['items'][0]
        self.assertEqual(citation['document_id'], uploaded['document_id'])
        self.assertEqual(citation['version'], 1)
        self.assertEqual(citation['name'], 'source.md')
        self.assertEqual(citation['revision'], listed['revision'])
        self.assertIn('characters', citation['location'])
        self.assertIn('CYAN', citation['excerpt'])
        with self.db.transaction() as c:
            object_id = c.execute(select(versions.c.object_id)).scalar()
        encrypted = self.runtime.storage.path(self.actor.owner_id, object_id).read_bytes()
        self.assertNotIn(b'CYAN', encrypted)
        downloaded = self.client.get(f'/v1/documents/{uploaded["document_id"]}/content', headers=self.headers)
        self.assertIn(b'CYAN', downloaded.content)
        self.assertEqual(downloaded.headers['x-content-sha256'], listed['sha256'])

    def test_foreign_document_storage_and_revision_conflict(self):
        uploaded = self.upload(self.collection())
        self.auth.provision('other-api-fixture', 'Other-Api-Fixture-Password-19')
        other = self.auth.login('other-api-fixture', 'Other-Api-Fixture-Password-19')
        headers = {'Authorization': 'Bearer ' + other['access_token']}
        response = self.client.get(f'/v1/documents/{uploaded["document_id"]}/content', headers=headers)
        self.assertEqual(response.status_code, 404)
        response = self.client.delete(f'/v1/documents/{uploaded["document_id"]}', params={'expected_revision': 999}, headers=self.headers)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get('/v1/documents', headers=headers).json()['items'], [])

    def test_delete_removes_source_index_and_propagates_tombstone(self):
        uploaded = self.upload(self.collection())
        self.runtime.worker.tick()
        row = self.client.get('/v1/documents', headers=self.headers).json()['items'][0]
        response = self.client.delete(f'/v1/documents/{uploaded["document_id"]}', params={'expected_revision': row['revision']}, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(list(self.runtime.storage.root.rglob('*.cxb')), [])
        result = self.client.post('/v1/knowledge/search', json={'query': 'CYAN'}, headers=self.headers).json()
        self.assertEqual(result['items'], [])
        self.assertTrue(result['insufficient_evidence'])

    def test_signature_path_request_limits_and_semantic_gate(self):
        collection = self.collection()
        for name, content in [('fake.pdf', b'Not a PDF'), ('../outside.txt', b'fixture'), ('archive.zip', b'PK')]:
            response = self.client.post(f'/v1/collections/{collection}/documents', params={'name': name}, content=content,
                headers={**self.headers, 'Idempotency-Key': str(uuid.uuid4())})
            self.assertIn(response.status_code, (415, 422), response.text)
        response = self.client.post('/v1/knowledge/search', json={'query': 'CYAN', 'mode': 'semantic'}, headers=self.headers)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['error']['code'], 'embedding_model_unconfigured')
        oversized = self.client.post('/v1/knowledge/search', content=b'x', headers={**self.headers, 'Content-Length': '999999999'})
        self.assertEqual(oversized.status_code, 413)

    def test_tls_required_and_no_unauthenticated_websocket(self):
        settings = replace(self.settings, require_tls=True)
        app = create_app(settings, runtime=self.runtime)
        client = TestClient(app, base_url='http://localhost')
        self.assertEqual(client.get('/v1/collections', headers=self.headers).status_code, 400)
        self.assertEqual(client.get('/healthz').status_code, 200)

    def test_structured_request_logs_never_contain_query_filename_body_or_bearer(self):
        import json
        with self.assertLogs('clydex.cloud.requests', level='INFO') as logged:
            self.client.get('/v1/documents', params={'collection_id': 'SYNTHETIC-PRIVATE-FILENAME'}, headers=self.headers)
            self.client.post('/v1/knowledge/search', json={'query': 'SYNTHETIC-PRIVATE-QUERY', 'unexpected': 'SYNTHETIC-PRIVATE-BODY'}, headers=self.headers)
        text = '\n'.join(logged.output)
        for secret in ('SYNTHETIC-PRIVATE-FILENAME', 'SYNTHETIC-PRIVATE-QUERY', 'SYNTHETIC-PRIVATE-BODY', self.tokens['access_token']):
            self.assertNotIn(secret, text)
        for record in logged.records:
            self.assertEqual(set(json.loads(record.getMessage())), {'request_id', 'method', 'route', 'status', 'duration_ms'})
