"""Real encrypted logical export/restore against isolated simulated SQL fixtures."""
from pathlib import Path
import unittest
import uuid
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from clydex_cloud.authentication.service import Authentication
from clydex_cloud.core.errors import CloudError
from clydex_cloud.repositories.database import Database
from clydex_cloud.repositories.migrate import migrate, rollback_empty, migration_hash
from clydex_cloud.repositories.schema import metadata, versions, sessions
from clydex_cloud.storage.files import FileStorage
from clydex_cloud.storage.recovery import export_recovery, restore_recovery
import test_api_vault


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        test_api_vault.ApiVaultTests.setUp(self)

    def test_packaged_mssql_constraint_names_are_schema_unique(self):
        # SQLite permits duplicate constraint names that SQL Server rejects.
        import re
        from clydex_cloud.repositories.migrate import script
        names = [str(constraint.name).casefold() for table in metadata.tables.values()
                 for constraint in table.constraints if constraint.name]
        self.assertEqual(len(names), len(set(names)), 'SQL Server constraint names must be schema-unique.')
        packaged = [name.casefold() for name in re.findall(r'CONSTRAINT\s+(\w+)', script())]
        self.assertEqual(len(packaged), len(set(packaged)))
        self.assertEqual(set(packaged), set(names))
        self.assertTrue(all(len(name) <= 128 for name in packaged))

    def test_restore_decrypts_original_document_but_revokes_old_sessions(self):
        collection = self.runtime.vault.create_collection(self.actor, {'title': 'Recovery fixture', 'description': ''})
        uploaded = self.runtime.vault.upload(self.actor, collection['id'], 'restore.txt', b'Original synthetic CYAN recovery evidence', str(uuid.uuid4()))
        export = Path(self.folder.name) / 'recovery.clxrec'
        export_recovery(self.db, self.runtime.storage, self.cipher, export, 'Synthetic-Recovery-Fixture-83')
        self.assertNotIn(b'Original synthetic', export.read_bytes())
        target = Database('', engine=create_engine('sqlite+pysqlite://', poolclass=StaticPool), test_only=True)
        self.addCleanup(target.close)
        self.assertTrue(migrate(target))
        self.assertFalse(migrate(target))
        storage = FileStorage(Path(self.folder.name) / 'restored-vault', 10 * 1024 * 1024)
        cipher = restore_recovery(target, storage, Path(self.folder.name) / 'restored-keys', export, 'Synthetic-Recovery-Fixture-83')
        auth = Authentication(target, cipher, self.settings)
        with self.assertRaises(CloudError):
            auth.authenticate(self.tokens['access_token'])
        auth.login('synthetic-owner', 'Synthetic-Login-Fixture-83')
        with target.transaction() as c:
            row = c.execute(select(versions).where(versions.c.document_id == uploaded['document_id'])).mappings().one()
            clear = storage.read(self.actor.owner_id, row['object_id'], cipher.owner_key(c, self.actor.owner_id), row['sha256'])
            self.assertEqual(clear, b'Original synthetic CYAN recovery evidence')
            self.assertIsNotNone(c.execute(select(sessions.c.revoked_at).where(sessions.c.id == self.actor.session_id)).scalar())
        with self.assertRaises(ValueError):
            restore_recovery(target, storage, Path(self.folder.name) / 'restored-keys', export, 'Synthetic-Recovery-Fixture-83')
        with self.assertRaises(ValueError):
            rollback_empty(target)

    def test_tamper_or_wrong_passphrase_cannot_restore_and_empty_rollback_works(self):
        export = Path(self.folder.name) / 'recovery.clxrec'
        export_recovery(self.db, self.runtime.storage, self.cipher, export, 'Synthetic-Recovery-Fixture-83')
        target = Database('', engine=create_engine('sqlite+pysqlite://', poolclass=StaticPool), test_only=True)
        self.addCleanup(target.close)
        migrate(target)
        storage = FileStorage(Path(self.folder.name) / 'bad-vault', 10 * 1024 * 1024)
        from cryptography.exceptions import InvalidTag
        with self.assertRaises(InvalidTag):
            restore_recovery(target, storage, Path(self.folder.name) / 'bad-keys', export, 'Wrong-Recovery-Fixture-83')
        data = bytearray(export.read_bytes())
        data[-1] ^= 1
        export.write_bytes(data)
        with self.assertRaises(InvalidTag):
            restore_recovery(target, storage, Path(self.folder.name) / 'bad-keys', export, 'Synthetic-Recovery-Fixture-83')
        self.assertEqual(list(storage.root.iterdir()), [])
        rollback_empty(target)
        self.assertEqual(len(migration_hash()), 64)

    def test_migration_failing_ddl_is_transactional_in_simulation(self):
        # SQLite transaction semantics are explicitly distinct from SQL Server.
        from unittest.mock import patch
        target = Database('', engine=create_engine('sqlite+pysqlite://', poolclass=StaticPool), test_only=True)
        self.addCleanup(target.close)
        with patch.object(metadata, 'create_all', side_effect=RuntimeError('synthetic migration failure')):
            with self.assertRaises(RuntimeError):
                migrate(target)
        self.assertFalse(target.ready())
        self.assertTrue(migrate(target))
