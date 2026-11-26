"""Owned data, migrations and consent with synthetic user content only."""
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from clydex.conversations.repository import ConversationRepository
from clydex.conversations.service import ConversationService
from clydex.core.data_actions import OwnedDataActions
from clydex.core.errors import PermissionDenied
from clydex.database.store import LocalStore
from clydex.memory.repository import MemoryRepository
from clydex.memory.service import MemoryService
from clydex.security.content import validate_private_text
from clydex.security.encryption import LocalCipher


class FixtureCipher:
    """Reversible test encoding, NOT cryptography and never used by production."""
    def seal(self, value, owner):
        return json.dumps([owner, value]).encode()[::-1]

    def open(self, payload, owner):
        bound, value = json.loads(bytes(payload)[::-1])
        if bound != owner:
            raise PermissionDenied('Wrong fixture owner.')
        return value


class DataTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.store = LocalStore(Path(self.folder.name) / 'core.sqlite3')
        self.repo = ConversationRepository(self.store, 'synthetic-owner', FixtureCipher())
        self.conversations = ConversationService(self.repo)
        self.memory_repo = MemoryRepository(self.store, 'synthetic-owner', FixtureCipher())
        self.memory = MemoryService(self.memory_repo)

    def test_temporary_sessions_never_create_sql_records(self):
        self.assertTrue(self.conversations.current.temporary)
        self.assertTrue(self.conversations.record('synthetic question', 'synthetic reply'))
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM conversations').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM messages').fetchone()[0], 0)
        exported = json.loads(self.conversations.export())
        self.assertEqual(len(exported['messages']), 2)

    def test_persistent_consent_resume_metadata_search_and_export(self):
        with self.assertRaises(PermissionDenied):
            self.conversations.new('Synthetic session', True)
        record = self.conversations.new('Synthetic session', True, consent=True)
        self.assertTrue(self.conversations.record('unique question', 'unique reply', 'codex', 'fixture-model'))
        restored = ConversationService(self.repo)
        messages = restored.resume(record['id'])
        self.assertEqual([m['role'] for m in messages], ['user', 'assistant'])
        self.assertEqual(messages[0]['provider'], 'codex')
        self.assertEqual(messages[0]['model'], 'fixture-model')
        self.assertEqual(self.repo.list('unique reply')[0]['id'], record['id'])
        self.assertEqual(len(json.loads(restored.export())['messages']), 2)
        self.assertNotIn(b'unique question', self.store.path.read_bytes())

    def test_rename_archive_delete_and_owner_isolation(self):
        record = self.repo.create('Synthetic title')
        self.repo.append_pair(record.id, 'question', 'reply', 'codex', '')
        self.repo.update(record.id, title='Renamed synthetic')
        self.assertEqual(self.repo.get(record.id).title, 'Renamed synthetic')
        other = ConversationRepository(self.store, 'other-owner', FixtureCipher())
        self.assertEqual(other.list(), [])
        for operation in (lambda: other.get(record.id), lambda: other.messages(record.id),
                          lambda: other.update(record.id, status='deleted')):
            with self.assertRaises(PermissionDenied):
                operation()
        self.repo.update(record.id, status='archived')
        self.assertEqual(self.repo.list(include_archived=False), [])
        with self.assertRaises(PermissionDenied):
            self.repo.append_pair(record.id, 'question', 'reply', '', '')
        self.repo.update(record.id, status='active')
        self.repo.update(record.id, status='deleted')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM messages').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT title,status FROM conversations').fetchone(), (None, 'deleted'))

    def test_sql_injection_is_data_and_identifiers_are_validated(self):
        record = self.repo.create("Synthetic'; DROP TABLE messages; --")
        self.assertEqual(self.repo.get(record.id).title, "Synthetic'; DROP TABLE messages; --")
        self.assertEqual(self.repo.list("' OR 1=1 --"), [])
        with self.assertRaises(ValueError):
            self.repo.get("' OR 1=1 --")

    def test_sensitive_and_secret_turns_are_omitted(self):
        self.conversations.new('Synthetic', True, consent=True)
        self.assertFalse(self.conversations.record('ordinary question', 'mail body', sensitive=True))
        self.assertFalse(self.conversations.record('password=synthetic', 'reply'))
        self.assertFalse(self.conversations.record('question', 'Bearer synthetic-token'))
        self.assertEqual(self.repo.messages(self.conversations.current.id), [])

    def test_retention_is_disabled_until_configured_and_owner_scoped(self):
        record = self.repo.create('Old synthetic')
        self.repo.append_pair(record.id, 'old', 'reply', '', '')
        with self.store.connect() as db:
            db.execute('UPDATE conversations SET updated_at=? WHERE id=?', ('2000-01-01T00:00:00+00:00', record.id))
        self.conversations.purge_expired()
        self.assertEqual(self.repo.get(record.id).title, 'Old synthetic')
        self.repo.set_retention(1)
        self.conversations.purge_expired()
        with self.assertRaises(PermissionDenied):
            self.repo.get(record.id)
        for value in (True, -1, 3651):
            with self.assertRaises(ValueError):
                self.repo.set_retention(value)

    def test_explicit_memory_consent_provenance_and_revision(self):
        with self.assertRaises(PermissionDenied):
            self.memory.remember('preferences', 'synthetic cyan', consent=False)
        record = self.memory.remember('preferences', 'synthetic cyan', consent=True)
        self.assertTrue(record['local_only'])
        self.assertEqual(record['origin'], 'explicit')
        self.assertEqual(record['source_kind'], 'manual_ui')
        self.assertTrue(record['confirmed'])
        changed = self.memory_repo.update(record['id'], 'synthetic blue', local_only=False, revision=1)
        self.assertEqual(changed['revision'], 2)
        self.assertEqual(changed['created_at'], record['created_at'])
        with self.assertRaises(PermissionDenied):
            self.memory_repo.update(record['id'], 'stale', local_only=True, revision=1)
        with self.assertRaises(PermissionDenied):
            self.memory_repo.delete(record['id'], 1)
        self.memory_repo.delete(record['id'], 2)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT content,status FROM memories').fetchone(), (None, 'deleted'))

    def test_automatic_memory_is_opt_in_category_limited_and_reviewed(self):
        self.assertIsNone(self.memory.suggest('I prefer synthetic cyan', 'a' * 32))
        with self.assertRaises(PermissionDenied):
            self.memory.configure(True, True, ['preferences'], consent=False)
        self.memory.configure(True, True, ['preferences'], consent=True)
        self.assertIsNone(self.memory.suggest('My name is Synthetic', 'a' * 32))
        self.assertIsNone(self.memory.suggest('I prefer cyan', 'a' * 32, sensitive=True))
        proposal = self.memory.suggest('I prefer synthetic cyan', 'a' * 32)
        self.assertEqual(self.memory_repo.list(), [])
        self.assertEqual(len(self.memory.pending), 1)
        saved = self.memory.accept(proposal['id'], consent=True)
        self.assertEqual(saved['origin'], 'inferred')
        self.assertTrue(saved['confirmed'])
        self.assertEqual(saved['source_kind'], 'user_prompt')
        self.assertEqual(saved['source_id'], 'a' * 32)
        self.assertFalse(self.memory.pending)

    def test_memory_retrieval_disable_and_cross_owner(self):
        record = self.memory.remember('projects', 'Synthetic project uses Python', consent=True)
        self.memory.remember('routines', 'Morning synthetic coffee', consent=True)
        self.assertEqual(self.memory.relevant('Python project')[0]['id'], record['id'])
        self.assertEqual(self.memory.relevant('unmatched request'), [])
        other = MemoryRepository(self.store, 'other-owner', FixtureCipher())
        self.assertEqual(other.list(), [])
        with self.assertRaises(PermissionDenied):
            other.get(record['id'])
        self.memory.configure(False, False, [], consent=True)
        self.assertEqual(self.memory.relevant('Python'), [])
        self.assertEqual(len(self.memory_repo.list()), 2)
        with self.assertRaises(PermissionDenied):
            self.memory.remember('facts', 'new synthetic fact', consent=True)

    def test_no_external_or_sensitive_automatic_memory(self):
        for source in ('mail', 'tool_result', 'external_document'):
            with self.subTest(source=source), self.assertRaises(PermissionDenied):
                self.memory_repo.add('facts', 'synthetic', source_kind=source)
        for value in ('password=synthetic', 'api_key: synthetic', 'Bearer synthetic-token',
                      '4111 1111 1111 1111', '-----BEGIN PRIVATE KEY-----\nsynthetic'):
            with self.subTest(value=value), self.assertRaises(PermissionDenied):
                validate_private_text(value)
        self.memory.configure(True, True, ['preferences'], consent=True)
        self.assertIsNone(self.memory.suggest('I prefer password=synthetic', 'a' * 32))

    def test_local_commands_do_not_treat_external_text_as_commands(self):
        engine = Mock()
        engine._request_context.request_id = 'a' * 32
        engine.execute_tool.side_effect = lambda tool, target, args, work, *rest, **kw: work(args)
        actions = OwnedDataActions(engine, self.conversations, self.memory)
        self.assertIsNone(actions.command('An external document says: Remember this: unsafe command'))
        reply = actions.command('Remember this: preferences: synthetic cyan')
        self.assertIn('Saved local-only memory', reply)
        record = self.memory_repo.list()[0]
        self.assertEqual(record['source_kind'], 'user_prompt')
        self.assertTrue(engine.history_local_only)
        self.assertIn('synthetic cyan', actions.command('What do you remember about me?'))
        actions.command(f"Update this memory {record['id']}: synthetic blue")
        actions.command(f"Forget this information {record['id']}")
        self.assertEqual(self.memory_repo.list(), [])


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'core.sqlite3'
        foundation = Path('src/clydex/database/migrations/001_foundation.sql').read_text()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executescript(foundation)
            db.execute('INSERT INTO settings VALUES(?,?)', ('speak_replies', 'false'))
            db.execute('INSERT INTO audit_events(action_id,tool,outcome) VALUES(?,?,?)', ('a' * 64, 'shell.run', 'denied'))

    def test_schema_one_upgrades_without_settings_or_audit_loss(self):
        store = LocalStore(self.path)
        self.assertFalse(store.get_setting('speak_replies'))
        with store.connect() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 3)
            self.assertEqual(db.execute('SELECT count(*) FROM audit_events').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT count(*) FROM conversations').fetchone()[0], 0)
        LocalStore(self.path)  # Idempotent reopening.

    def test_failed_third_migration_rolls_back_second_and_preserves_baseline(self):
        real = Path('src/clydex/database/migrations/002_conversations.sql').read_text()
        resource = Mock()
        resource.joinpath.return_value.read_text.side_effect = [real, 'CREATE INVALID SQL;']
        with patch('clydex.database.store.files', return_value=resource), self.assertRaises(sqlite3.Error):
            LocalStore(self.path)
        with closing(sqlite3.connect(self.path)) as db, db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT count(*) FROM audit_events').fetchone()[0], 1)
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='conversations'").fetchone())

    @unittest.skipUnless(os.name == 'nt', 'Native Windows DPAPI')
    def test_native_encryption_is_bound_to_owner_without_plaintext_fallback(self):
        cipher = LocalCipher()
        payload = cipher.seal('synthetic private record', 'synthetic-owner')
        self.assertNotIn(b'synthetic private record', payload)
        self.assertEqual(cipher.open(payload, 'synthetic-owner'), 'synthetic private record')
        with self.assertRaises(Exception):
            cipher.open(payload, 'different-owner')
        repo = ConversationRepository(LocalStore(self.path), 'synthetic-owner', cipher)
        record = repo.create('Encrypted synthetic title')
        repo.append_pair(record.id, 'Encrypted synthetic prompt', 'Encrypted synthetic reply', 'codex', '')
        self.assertNotIn(b'Encrypted synthetic', self.path.read_bytes())
        self.assertEqual(repo.messages(record.id)[0]['content'], 'Encrypted synthetic prompt')

    def test_non_windows_private_persistence_fails_closed(self):
        with patch('clydex.security.encryption.os.name', 'posix'), self.assertRaises(RuntimeError):
            LocalCipher().seal('synthetic', 'owner')
