from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import io
import importlib.util
import json
import logging
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from clydex.core.config import AppConfig, RuntimePaths
from clydex.core.contracts import ActionRequest, RequestContext
from clydex.core.errors import failure_for
from clydex.core.events import CoreEvent, EventChannel
from clydex.core.logging import SafeFormatter
from clydex.database.store import LocalStore
from clydex.security.credentials import CredentialStore


class ConfigurationTests(unittest.TestCase):
    def test_strict_flags_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = RuntimePaths(Path(folder))
            paths.ensure()
            self.assertFalse(AppConfig.load(paths, {'CLYDEX_ALLOW_CLOUD': 'false'}).allow_cloud)
            with self.assertRaises(ValueError):
                AppConfig.load(paths, {'CLYDEX_ALLOW_CLOUD': 'yes'})
            (paths.directory('settings') / 'config.json').write_text('{"api_key":"private"}')
            with self.assertRaises(ValueError):
                AppConfig.load(paths, {})

    def test_runtime_layout_and_path_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = RuntimePaths(Path(folder) / 'CLYDEX')
            paths.ensure()
            self.assertEqual(len(list(paths.root.iterdir())), 9)
            with self.assertRaises(ValueError):
                paths.directory('../outside')
        with patch.dict(os.environ, {'LOCALAPPDATA': 'relative'}):
            with self.assertRaises(ValueError):
                RuntimePaths.for_user()
        with self.assertRaises(ValueError):
            RuntimePaths(Path.cwd() / 'runtime').ensure()

    def test_invalid_types_ranges_and_voice(self):
        for kwargs in ({'allow_cloud': 'false'}, {'approval_timeout': True},
                       {'event_capacity': 0}, {'recognition_mode': 'unsupported'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                AppConfig(**kwargs)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'core.sqlite3'
        self.store = LocalStore(self.path)

    def test_reopen_settings_and_foreign_keys(self):
        self.store.set_setting('recognition_mode', 'en-accurate')
        store = LocalStore(self.path)
        self.assertEqual(store.get_setting('recognition_mode'), 'en-accurate')
        with store.connect() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)
            self.assertEqual(db.execute('PRAGMA foreign_keys').fetchone()[0], 1)

    def test_secrets_and_arbitrary_audit_content_rejected(self):
        with self.assertRaises(ValueError):
            self.store.set_setting('password', 'private')
        with self.assertRaises(ValueError):
            self.store.set_setting('recognition_mode', 'private')
        with self.assertRaises(ValueError):
            self.store.audit('a' * 64, 'mail.read', 'private content')
        self.store.audit('a' * 64, 'mail.read', 'executed')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT tool,outcome FROM audit_events').fetchall(),
                             [('mail.read', 'executed')])

    def test_newer_database_is_not_downgraded(self):
        with self.store.connect() as db:
            db.execute('PRAGMA user_version=2')
        with self.assertRaises(RuntimeError):
            LocalStore(self.path)
        with self.store.connect() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 2)

    def test_failed_migration_rolls_back(self):
        other = Path(self.folder.name) / 'failed.sqlite3'
        resource = Mock()
        resource.joinpath.return_value.read_text.return_value = 'CREATE TABLE partial(x); INVALID SQL;'
        with patch('clydex.database.store.files', return_value=resource):
            with self.assertRaises(sqlite3.Error):
                LocalStore(other)
        with closing(sqlite3.connect(other)) as db:
            self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE name='partial'").fetchall(), [])
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 0)

    def test_concurrent_open_and_writes(self):
        def write(_):
            LocalStore(self.path).set_setting('speak_replies', False)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(write, range(12)))
        self.assertIs(self.store.get_setting('speak_replies'), False)


class CommunicationAndPrivacyTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('numpy'), 'Optional desktop audio dependency')
    def test_audio_spectrum_uses_real_sample_energy(self):
        import numpy as np
        from clydex.voice.spectrum import SpectrumStream
        stream = SpectrumStream(16000)
        samples = .1 * np.sin(2 * np.pi * 1000 * np.arange(2048) / 16000)
        stream.push(samples)
        level, bands, wave = stream.read_display()
        self.assertAlmostEqual(level, .1 / np.sqrt(2), places=3)
        self.assertEqual(len(bands), 36)
        self.assertGreater(max(bands), 0)
        self.assertEqual(len(wave), 256)

    def test_event_backpressure_keeps_done_and_latest_status(self):
        events = EventChannel(8)
        for i in range(100):
            events.put(CoreEvent('status', i))
        self.assertEqual(events.qsize(), 1)
        for i in range(20):
            events.put(('bot', str(i)))
        events.put(('done', None))
        self.assertLessEqual(events.qsize(), 8)
        self.assertGreater(events.dropped, 0)
        result = [events.get_nowait() for _ in range(events.qsize())]
        self.assertEqual(result[-1], ('done', None))

    def test_logs_drop_arbitrary_messages_extras_and_exception_text(self):
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(SafeFormatter())
        logger = logging.Logger('test')
        logger.addHandler(handler)
        try:
            raise RuntimeError('private-token mailbox contents')
        except RuntimeError:
            logger.exception('private-token', extra={'prompt': 'mailbox contents'})
        row = json.loads(output.getvalue())
        self.assertEqual(row['event'], 'diagnostic')
        self.assertNotIn('private-token', output.getvalue())
        self.assertNotIn('mailbox', output.getvalue())
        self.assertNotIn('private-token', failure_for(RuntimeError('private-token')).message)

    def test_action_detaches_input_and_hashes_canonical_payload(self):
        context = RequestContext('local-user', 'desktop', 'request')
        args = {'script': 'Write-Output hello'}
        action = ActionRequest.create('shell.run', 'profile', args, context)
        args['script'] = 'changed'
        self.assertEqual(action.arguments['script'], 'Write-Output hello')
        self.assertEqual(len(action.digest), 64)
        with self.assertRaises(ValueError):
            ActionRequest.create('shell.run', 'profile', {'bad': float('nan')}, context)

    def test_credential_identifiers_do_not_allow_path_or_arbitrary_targets(self):
        for name in ('../outside', '', 'https://example.com'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                CredentialStore().get(name)

    @unittest.skipUnless(os.name == 'nt' and importlib.util.find_spec('win32cred'),
                         'Windows Credential Manager API mock')
    def test_credential_manager_roundtrip_uses_no_plaintext_file(self):
        store = CredentialStore()
        with patch('win32cred.CredWrite') as write, patch('win32cred.CredRead') as read:
            store.set('test.provider', 'test-only-secret')
            self.assertIsInstance(write.call_args.args[0]['CredentialBlob'], str)
            read.return_value = {'CredentialBlob': write.call_args.args[0]['CredentialBlob']}
            self.assertEqual(store.get('test.provider'), 'test-only-secret')
            self.assertEqual(write.call_args.args[0]['TargetName'], 'CLYDEX/test.provider')
