from pathlib import Path
import queue
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from clydex.core.application import CoreApplication
from clydex.core.config import AppConfig, RuntimePaths
from clydex.core.instance import InstanceLock
from clydex.desktop.studio import Studio
from tests.test_regression import engine_for_test


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.paths = RuntimePaths(Path(self.folder.name))
        self.engine = engine_for_test()
        with patch('clydex.core.application.legacy_recognition_mode', return_value='en-accurate'):
            self.core = CoreApplication(paths=self.paths, engine=self.engine)
        self.addCleanup(self.core.close)
        self.studio = Studio(self.core)

    def test_legacy_preference_import_then_sqlite_precedence(self):
        self.assertEqual(self.engine.speech_mode, 'en-accurate')
        self.assertEqual(self.studio.recognition_mode('auto'), 'auto')
        self.assertEqual(self.core.store.get_setting('recognition_mode'), 'auto')
        self.assertTrue(self.studio.speak_replies(False))
        self.core.close()
        with patch('clydex.core.application.legacy_recognition_mode', return_value='en'):
            reopened = CoreApplication(paths=self.paths, engine=engine_for_test())
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.engine.speech_mode, 'auto')
        self.assertFalse(reopened.engine.speak_preference)

    def test_only_one_core_can_own_user_runtime(self):
        with self.assertRaises(RuntimeError):
            CoreApplication(paths=self.paths, engine=engine_for_test())
        self.core.close()
        another = CoreApplication(paths=self.paths, engine=engine_for_test())
        another.close()

    def test_failed_configuration_releases_instance_lock(self):
        self.core.close()
        file = self.paths.directory('settings') / 'config.json'
        file.write_text('{"password":"forbidden"}')
        with self.assertRaises(ValueError):
            CoreApplication(paths=self.paths, engine=engine_for_test())
        lock = InstanceLock(self.paths.directory('settings') / 'core.lock')
        lock.close()

    def test_studio_text_flow_and_clear_use_core(self):
        self.engine.provider.respond.return_value = {'steps': [], 'message': 'hello'}
        self.assertFalse(self.studio.send(12))
        self.assertFalse(self.studio.send(''))
        self.assertTrue(self.studio.send('Hello'))
        deadline = time.monotonic() + 2
        messages = []
        while time.monotonic() < deadline:
            snapshot = self.studio.snapshot()
            messages.extend(snapshot['messages'])
            if not snapshot['busy']:
                break
            time.sleep(.005)
        self.assertIn(['bot', 'hello'], messages)
        self.assertFalse(snapshot['busy'])
        self.assertTrue(self.studio.clear())
        self.assertEqual(self.engine.history, [])

    def test_unhandled_worker_failure_is_mapped_and_ui_becomes_ready(self):
        def fail():
            raise RuntimeError('never expose private value')
        handle = self.core.submit(fail)
        with self.assertRaises(RuntimeError):
            handle.future.result(2)
        # Future callbacks can finish just after result(); wait for event delivery.
        deadline = time.monotonic() + 2
        while self.engine.events.qsize() < 2 and time.monotonic() < deadline:
            time.sleep(.005)
        snapshot = self.studio.snapshot()
        self.assertFalse(snapshot['busy'])
        self.assertNotIn('private value', repr(snapshot))
        self.assertTrue(any(row[0] == 'error' for row in snapshot['messages']))

    def test_stop_after_submit_prevents_or_cancels_work(self):
        entered = threading.Event()
        def work():
            entered.set()
            while not self.engine.cancel_token.is_set():
                time.sleep(.005)
            self.engine.events.put(('done', None))
        self.assertTrue(self.studio._start('THINKING', work))
        self.assertTrue(entered.wait(2))
        self.assertTrue(self.studio.stop())
        deadline = time.monotonic() + 2
        while self.studio.snapshot()['busy'] and time.monotonic() < deadline:
            time.sleep(.005)
        self.assertFalse(self.studio.snapshot()['busy'])

    def test_core_close_is_idempotent_and_queue_rejects_new_work(self):
        self.core.close()
        self.core.close()
        with self.assertRaises(RuntimeError):
            self.core.submit(lambda: None)

    def test_queue_full_is_reported_to_desktop_without_new_thread(self):
        with patch.object(self.core, 'submit', side_effect=queue.Full):
            self.assertFalse(self.studio.send('Hello'))
        self.assertFalse(self.studio.snapshot()['busy'])

    def test_policy_config_never_enables_cloud_in_privacy_mode(self):
        self.engine.config = AppConfig(privacy_mode=True)
        self.assertTrue(self.studio.send('Hello'))
        deadline = time.monotonic() + 2
        messages = []
        while time.monotonic() < deadline:
            snapshot = self.studio.snapshot()
            messages.extend(snapshot['messages'])
            if not snapshot['busy']:
                break
            time.sleep(.005)
        self.assertTrue(any(row[0] == 'error' for row in messages))
        self.engine.provider.respond.assert_not_called()
