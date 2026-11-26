"""Real loopback HTTP against synthetic fixtures, never external AI services."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timedelta, timezone
import http.client
import ipaddress
import json
from pathlib import Path
import ssl
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from clydex.automation.tasks import CancellationToken
from clydex.core.errors import Cancelled
from clydex.providers.base import ProviderFailure
from clydex.providers.ollama_provider import OllamaProvider
from clydex.providers.transport import HTTPTransport
from tests.test_intelligence import ANSWER, REQUEST, Credentials, configured, envelope


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.handle_fixture()

    def do_POST(self):
        self.handle_fixture()

    def handle_fixture(self):
        length = int(self.headers.get('Content-Length', 0))
        self.server.captured.append((self.path, self.rfile.read(length), dict(self.headers)))
        self.server.entered.set()
        try:
            self.send_response(self.server.status)
            self.send_header('Content-Type', 'application/json')
            if self.server.chunked:
                self.send_header('Transfer-Encoding', 'chunked')
            else:
                self.send_header('Content-Length', str(len(self.server.body)))
            self.end_headers()
            if self.server.delay:
                self.server.release.wait(2)
            if self.server.chunked:
                for offset in range(0, len(self.server.body), 127):
                    part = self.server.body[offset:offset + 127]
                    self.wfile.write(format(len(part), 'x').encode() + b'\r\n' + part + b'\r\n')
                self.wfile.write(b'0\r\n\r\n')
            else:
                self.wfile.write(self.server.body)
            self.wfile.flush()
        except OSError:
            pass


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.status, self.server.body, self.server.delay = 200, b'{"synthetic":true}', False
        self.server.chunked = False
        self.server.captured = []
        self.server.entered, self.server.release = threading.Event(), threading.Event()
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .02})
        self.thread.start()
        self.addCleanup(self.close)
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.transport, self.token = HTTPTransport(), CancellationToken()

    def close(self):
        self.server.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    def request(self, **values):
        args = dict(method='GET', url=self.url, headers={}, body=None, cancel=self.token, timeout=1, limit=4096)
        args.update(values)
        return self.transport.request(**args)

    def test_real_ollama_serialization_and_validated_response(self):
        self.server.body = json.dumps(envelope('ollama')).encode()
        config = configured('ollama', endpoint=self.url)
        provider = OllamaProvider(config, Credentials())
        self.assertEqual(provider.respond(REQUEST, self.token), ANSWER)
        path, body, headers = self.server.captured[0]
        self.assertEqual(path, '/api/chat')
        self.assertEqual(json.loads(body)['model'], 'fixture-model')
        self.assertNotIn('Authorization', headers)

    def test_status_errors_are_normalized_without_body_exposure_or_redirect(self):
        self.server.body = b'never expose this private fixture'
        for status, kind in ((401, 'authentication'), (403, 'authentication'), (404, 'model_unavailable'),
                             (429, 'rate_limit'), (500, 'service_error'), (302, 'service_error')):
            self.server.status = status
            before = len(self.server.captured)
            with self.subTest(status=status), self.assertRaises(ProviderFailure) as failure:
                self.request()
            self.assertEqual(failure.exception.kind, kind)
            self.assertNotIn('private fixture', str(failure.exception))
            self.assertEqual(len(self.server.captured), before + 1)

    def test_stream_chunks_and_response_limit(self):
        self.server.body = b'x' * 12000
        chunks = []
        self.assertEqual(self.request(receive=chunks.append, limit=16000), b'')
        self.assertEqual(b''.join(chunks), self.server.body)
        with self.assertRaises(ProviderFailure) as failure:
            self.request(limit=1000)
        self.assertEqual(failure.exception.kind, 'response_limit')

    def test_total_timeout_interrupts_stalled_response(self):
        self.server.delay = True
        start = time.monotonic()
        with self.assertRaises(ProviderFailure) as failure:
            self.request(timeout=.15)
        self.assertEqual(failure.exception.kind, 'timeout')
        self.assertLess(time.monotonic() - start, 1)

    def test_cancel_interrupts_stalled_response(self):
        self.server.delay = True
        outcomes = []
        def work():
            try:
                self.request(timeout=2)
            except Exception as exc:
                outcomes.append(exc)
        worker = threading.Thread(target=work)
        worker.start()
        self.assertTrue(self.server.entered.wait(1))
        self.token.set()
        worker.join(1)
        self.assertFalse(worker.is_alive())
        self.assertIsInstance(outcomes[0], Cancelled)

    def test_precancel_and_insecure_endpoint_never_connect(self):
        self.token.set()
        with self.assertRaises(Cancelled):
            self.request()
        self.assertFalse(self.server.captured)
        with self.assertRaises(ProviderFailure):
            self.request(cancel=CancellationToken(), url='http://external.invalid')

    def test_network_failure_and_cancellation_during_connect(self):
        with patch.object(self.transport, '_connect_socket', side_effect=ConnectionRefusedError), self.assertRaises(ProviderFailure) as failure:
            self.request()
        self.assertEqual(failure.exception.kind, 'network')
        def canceled_connect(*args):
            self.token.set()
        with patch.object(self.transport, '_connect_socket', side_effect=canceled_connect), self.assertRaises(Cancelled):
            self.request()
        self.assertFalse(self.server.captured)

    def test_cancel_after_http10_connection_releases_its_socket_facade(self):
        self.server.delay = True
        entered, outcomes = threading.Event(), []
        original = http.client.HTTPResponse.read1
        def read(response, size):
            entered.set()
            return original(response, size)
        def work():
            try:
                self.request(timeout=2)
            except Exception as exc:
                outcomes.append(exc)
        with patch.object(http.client.HTTPResponse, 'read1', read):
            worker = threading.Thread(target=work)
            worker.start()
            self.assertTrue(entered.wait(1))
            self.token.set()
            worker.join(1)
        self.assertFalse(worker.is_alive())
        self.assertIsInstance(outcomes[0], Cancelled)

    def test_chunked_response_framing_uses_standard_parser(self):
        self.server.chunked, self.server.body = True, b'fixture' * 1000
        self.assertEqual(self.request(limit=10000), self.server.body)

    def test_verified_local_tls_read_and_cancellation(self):
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        with tempfile.TemporaryDirectory() as directory:
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'CLYDEX synthetic TLS fixture')])
            now = datetime.now(timezone.utc)
            cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
                .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=1))
                .not_valid_after(now + timedelta(days=1)).add_extension(x509.SubjectAlternativeName([
                    x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False).sign(key, hashes.SHA256()))
            cert_path, key_path = Path(directory) / 'fixture-cert.pem', Path(directory) / 'fixture-key.pem'
            cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
            key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                                   serialization.NoEncryption()))
            server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            server_context.load_cert_chain(str(cert_path), str(key_path))
            self.server.socket = server_context.wrap_socket(self.server.socket, server_side=True)
            client_context = ssl.create_default_context(cafile=str(cert_path))
            url = self.url.replace('http:', 'https:')
            with patch('clydex.providers.transport.ssl.create_default_context', return_value=client_context):
                self.assertEqual(self.request(url=url), self.server.body)
                self.server.delay = True
                self.server.entered.clear()
                outcomes = []
                def work():
                    try:
                        self.request(url=url, timeout=2)
                    except Exception as exc:
                        outcomes.append(exc)
                worker = threading.Thread(target=work)
                worker.start()
                self.assertTrue(self.server.entered.wait(1))
                self.token.set()
                worker.join(1)
                self.server.release.set()
                self.assertFalse(worker.is_alive())
                self.assertIsInstance(outcomes[0], Cancelled)
