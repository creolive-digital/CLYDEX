"""Synthetic SQL repository simulation, not native SQL Server verification."""
import os
from pathlib import Path
import tempfile
import unittest
from cryptography.exceptions import InvalidTag

from sqlalchemy import create_engine, event, insert
from sqlalchemy.pool import StaticPool

from clydex_cloud.authentication.service import Authentication
from clydex_cloud.core.config import Settings
from clydex_cloud.core.encryption import VaultCipher
from clydex_cloud.core.errors import CloudError
from clydex_cloud.devices.service import DeviceService
from clydex_cloud.repositories.database import Database
from clydex_cloud.repositories.schema import metadata, schema_versions


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix='clydex-cloud-security-')
        self.addCleanup(self.folder.cleanup)
        self.settings = Settings(Path(self.folder.name) / 'data', Path(self.folder.name) / 'keys',
                                 environment='test', require_tls=False)
        engine = create_engine('sqlite+pysqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
        @event.listens_for(engine, 'connect')
        def enable_foreign_keys(connection, record):
            connection.execute('PRAGMA foreign_keys=ON')
        metadata.create_all(engine)
        self.db = Database('', engine=engine, test_only=True)
        self.addCleanup(self.db.close)
        with self.db.transaction() as c:
            c.execute(insert(schema_versions).values(version=1, sha256='0' * 64, applied_at=1))
        self.cipher = VaultCipher(os.urandom(32), os.urandom(32))
        self.auth = Authentication(self.db, self.cipher, self.settings)
        self.owner = self.auth.provision('synthetic-owner', 'Synthetic-Login-Fixture-83')
        self.tokens = self.auth.login('synthetic-owner', 'Synthetic-Login-Fixture-83')
        self.actor = self.auth.authenticate(self.tokens['access_token'])
        self.devices = DeviceService(self.db, self.cipher, self.auth)

    def test_short_lived_tokens_refresh_rotation_and_reuse_revocation(self):
        rotated = self.auth.rotate(self.tokens['refresh_token'])
        with self.assertRaises(CloudError):
            self.auth.authenticate(self.tokens['access_token'])
        self.auth.authenticate(rotated['access_token'])
        with self.assertRaises(CloudError) as reused:
            self.auth.rotate(self.tokens['refresh_token'])
        self.assertEqual(reused.exception.code, 'refresh_reuse_revoked')
        with self.assertRaises(CloudError):
            self.auth.authenticate(rotated['access_token'])

    def test_pairing_needs_approval_and_device_revocation_is_immediate(self):
        pairing = self.devices.request_pairing(self.actor, {'display_name': 'Synthetic Windows', 'platform': 'Windows'}, ['vault.read'])
        with self.assertRaises(CloudError):
            self.devices.claim(pairing['pairing_token'])
        self.devices.approve(self.actor, pairing['id'])
        tokens = self.devices.claim(pairing['pairing_token'])
        device = self.auth.authenticate(tokens['access_token'])
        self.assertEqual(device.scopes, frozenset(('vault.read',)))
        with self.assertRaises(CloudError):
            device.require('devices.manage')
        with self.assertRaises(CloudError):
            self.devices.claim(pairing['pairing_token'])
        self.devices.revoke(self.actor, device.device_id)
        for work in (lambda: self.auth.authenticate(tokens['access_token']), lambda: self.auth.rotate(tokens['refresh_token'])):
            with self.assertRaises(CloudError):
                work()

    def test_account_recovery_revokes_sessions_and_rotates_one_time_code(self):
        recovered = self.auth.recover('synthetic-owner', self.owner['recovery_code'], 'Replacement-Fixture-Password-92')
        self.assertNotEqual(recovered['recovery_code'], self.owner['recovery_code'])
        with self.assertRaises(CloudError):
            self.auth.authenticate(self.tokens['access_token'])
        with self.assertRaises(CloudError):
            self.auth.recover('synthetic-owner', self.owner['recovery_code'], 'Never-Accept-This-Fixture-03')

    def test_encrypted_payload_is_bound_to_owner_and_role(self):
        other = self.auth.provision('synthetic-other', 'Other-Fixture-Password-73')
        with self.db.transaction() as c:
            encrypted = self.cipher.seal(c, self.actor.owner_id, 'fixture', {'text': 'Synthetic private content'})
            self.assertNotIn(b'Synthetic private content', encrypted)
            self.assertEqual(self.cipher.open(c, self.actor.owner_id, 'fixture', encrypted)['text'], 'Synthetic private content')
            for owner, role in ((other['account_id'], 'fixture'), (self.actor.owner_id, 'wrong-role')):
                with self.assertRaises(InvalidTag):
                    self.cipher.open(c, owner, role, encrypted)

    def test_no_insecure_production_or_unrequested_primary_database_substitution(self):
        with self.assertRaises(ValueError):
            Settings(self.settings.data_root, self.settings.secrets_root, require_tls=False)
        with self.assertRaises(ValueError):
            Database('sqlite:///never-production.db')
        self.assertTrue(self.db.simulated)
        self.assertTrue(self.db.ready())
