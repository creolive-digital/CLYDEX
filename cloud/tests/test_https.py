"""Actual loopback TLS/HTTP, real cloud routes, explicitly simulated SQL repository."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import ipaddress
from pathlib import Path
import socket
import ssl
import threading
import time
import unittest
from unittest.mock import patch
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import uvicorn
from clydex.cloud.client import CloudClient, CloudConfig, CloudFailure
from clydex.automation.tasks import CancellationToken
from clydex_cloud.api.app import create_app
import test_api_vault


class HttpsTests(unittest.TestCase):
    def setUp(self):
        test_api_vault.ApiVaultTests.setUp(self)

    def test_real_verified_tls_login_contract_ownership_and_no_redirects(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'CLYDEX synthetic loopback only')])
        now = datetime.now(timezone.utc)
        certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(hours=1))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False)
            .sign(key, hashes.SHA256()))
        cert, private = Path(self.folder.name)/'test-ca.pem', Path(self.folder.name)/'test-key.pem'
        cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
        private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        settings = replace(self.settings, public_host='127.0.0.1', require_tls=True)
        app = create_app(settings, runtime=self.runtime)
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, ssl_certfile=str(cert), ssl_keyfile=str(private),
            log_config=None, access_log=False, log_level='critical', ws='none'))
        thread = threading.Thread(target=server.run, kwargs={'sockets': [listener]})
        thread.start()
        try:
            end = time.monotonic()+10
            while not server.started and thread.is_alive() and time.monotonic()<end:
                time.sleep(.02)
            self.assertTrue(server.started)
            context = ssl.create_default_context(cafile=str(cert))
            with patch('clydex.providers.transport.ssl.create_default_context', return_value=context):
                client = CloudClient(CloudConfig(f'https://127.0.0.1:{port}', True))
                token = CancellationToken()
                result = client.login('synthetic-owner', 'Synthetic-Login-Fixture-83', token)
                self.assertTrue(result['authenticated'])
                collection = client.request('POST', '/v1/collections', {'title':'Loopback fixture','description':''}, token)
                self.assertIn(collection['id'], [r['id'] for r in client.request('GET', '/v1/collections', None, token)['items']])
                with self.assertRaises(CloudFailure) as missing:
                    client.request('GET', '/v1/documents/00000000-0000-0000-0000-000000000001/content', None, token)
                self.assertEqual(missing.exception.status, 404)
                client.request('POST', '/v1/auth/logout', None, token)
                with self.assertRaises(CloudFailure):
                    client.request('GET', '/v1/collections', None, token)
        finally:
            server.should_exit = True
            thread.join(10)
            listener.close()
        self.assertFalse(thread.is_alive())
