"""Headless HUD contract, privacy, configuration and display tests. No audio/network."""
from dataclasses import asdict, replace
import mimetypes
from pathlib import Path
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from clydex.core.application import CoreApplication
from clydex.core.config import RuntimePaths
from clydex.desktop.display import DisplayController, clamp_geometry
from clydex.desktop.hud import CONTRACT, HudBridge, HudService, validate_packet
from clydex.desktop.notifications import NotificationCenter
from clydex.desktop.preferences import PresentationPreferences
from clydex.core.errors import PermissionDenied
from tests.test_personal_data import FixtureCipher
from tests.test_regression import engine_for_test


class HudTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.paths = RuntimePaths(Path(self.folder.name))
        self.engine = engine_for_test()
        with patch('clydex.core.application.LocalCipher', FixtureCipher):
            self.core = CoreApplication(paths=self.paths, engine=self.engine)
        self.addCleanup(self.core.close)
        from clydex.desktop.studio import Studio
        self.studio = Studio(self.core)
        self.widget = Mock()
        self.widget.snapshot.return_value = {'status': 'not_started', 'alerts': []}
        self.hud = HudService(self.studio, widget=self.widget, start=False)
        self.api = HudBridge(self.hud)

    def settle(self, approve):
        seen = []
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            review = self.engine.pending_review()
            if review:
                seen.append(review)
                self.studio.decide(review['id'], approve)
            self.hud.collect()
            if not self.core.queue.busy:
                return seen
            time.sleep(.005)
        self.core.stop()
        self.fail('HUD task did not settle.')

    def test_bridge_exposes_only_three_entrypoints_and_rejects_unknown_fields(self):
        self.assertEqual([x for x in dir(self.api) if not x.startswith('_')], ['hud_command', 'hud_read', 'hud_snapshot'])
        for action, payload in [('__class__', {}), ('shell.run', {'script': 'never execute'}),
                                ('chat.send', {'message': 'fixture', 'risk': 'low'}),
                                ('voice.mute', {'muted': 1}), ('display.monitor', {'index': True}),
                                ('preferences.configure', {'values': {'fps': float('nan')}})]:
            self.assertFalse(self.api.hud_command(action, payload)['ok'])
        self.assertFalse(self.core.queue.busy)

    def test_contract_is_packaged_and_request_size_is_bounded(self):
        self.assertEqual(CONTRACT['version'], 1)
        self.assertEqual(mimetypes.guess_type('client.js')[0], 'text/javascript')
        with self.assertRaises(ValueError):
            validate_packet('command', 'chat.send', {'message': 'a' * 65536})

    def test_playback_counters_are_observed_events_not_estimated_lip_sync(self):
        self.core.voice.events.emit('playback_started', sample_rate=24000)
        self.hud.collect()
        self.assertEqual(self.hud.snapshot()['playback'], dict(frames_played=0, sample_rate=24000, completed=None))
        self.core.voice.events.emit('playback_stopped', frames_played=3840, completed=False)
        self.hud.collect()
        self.assertEqual(self.hud.snapshot()['playback']['frames_played'], 3840)
        self.assertFalse(self.hud.snapshot()['playback']['completed'])
        self.assertFalse(self.api.hud_read('filesystem', {'path': 'private'})['ok'])

    def test_startup_reports_local_readiness_and_voice_provider_gates_without_network(self):
        self.core.providers.build = Mock(side_effect=AssertionError('No startup inference'))
        result = self.api.hud_read('bootstrap')['data']
        states = {row['component']: row for row in result['initialization']}
        self.assertEqual(states['Database']['detail'], 'Schema 3')
        self.assertEqual(states['Providers']['status'], 'unverified')
        self.assertEqual(states['Voice']['status'], 'gated')
        self.core.providers.build.assert_not_called()
        self.assertFalse(self.core.voice.config.microphone_enabled)

    def test_configuration_requires_exact_review_and_denial_preserves_preferences(self):
        before = asdict(self.hud.preferences.values)
        self.assertTrue(self.api.hud_command('preferences.configure', {'values': {'sound_volume': 31}})['ok'])
        reviews = self.settle(False)
        self.assertIn('desktop.configure', reviews[0]['script'])
        self.assertEqual(asdict(self.hud.preferences.values), before)
        self.assertTrue(self.api.hud_command('preferences.configure', {'values': {'sound_volume': 31}})['ok'])
        self.settle(True)
        self.assertEqual(self.hud.preferences.values.sound_volume, 31)
        self.assertTrue(self.hud.preferences.values.sounds_muted)

    def test_permissions_can_restrict_but_cannot_remove_startup_ceiling(self):
        self.core.config = replace(self.core.config, disabled_scopes=('shell.powershell',))
        self.api.hud_command('permissions.configure', {'disabled_scopes': ['apps.launch']})
        self.settle(True)
        self.assertIn('apps.launch', self.engine.executor._disabled_scopes)
        self.assertIn('shell.powershell', self.engine.executor._disabled_scopes)
        self.api.hud_command('permissions.configure', {'disabled_scopes': []})
        self.settle(True)
        self.assertNotIn('apps.launch', self.engine.executor._disabled_scopes)
        self.assertIn('shell.powershell', self.engine.executor._disabled_scopes)

    def test_lock_redacts_all_private_frame_data_and_rejects_reads(self):
        self.engine.events.put(('user', 'synthetic private text'))
        self.hud.collect()
        self.assertTrue(self.api.hud_snapshot()['messages'])
        self.hud.notifications.add('approval.waiting')
        self.core.voice.privacy.probe = lambda: True
        frame = self.api.hud_snapshot()
        self.assertTrue(frame['locked'])
        self.assertEqual(frame['messages'], [])
        self.assertEqual(frame['notifications'], [])
        self.assertIsNone(frame['review'])
        self.assertFalse(self.api.hud_read('memories')['ok'])
        self.assertFalse(self.api.hud_command('chat.send', {'message': 'never send'})['ok'])
        self.assertTrue(self.api.hud_command('voice.stop')['ok'])
        self.assertTrue(self.api.hud_command('voice.mute', {'muted': True})['ok'])

    def test_bounded_notifications_never_accept_private_messages(self):
        center = NotificationCenter()
        for _ in range(120):
            center.add('task.complete')
        self.assertEqual(len(center.snapshot()), 100)
        with self.assertRaises(ValueError):
            center.add('private transcript text')

    def test_one_collector_retains_chat_and_uses_actual_audio(self):
        self.engine.events.put(('bot', 'Synthetic answer'))
        self.hud.collect()
        first = self.api.hud_snapshot()
        second = self.api.hud_snapshot()
        self.assertEqual(first['messages'], second['messages'])
        self.assertEqual(second['messages'][0]['text'], 'Synthetic answer')
        self.assertEqual(second['level'], 0)
        self.assertEqual(second['bands'], [])
        self.assertTrue(self.api.hud_command('chat.clear')['ok'])
        self.assertEqual(self.api.hud_snapshot()['messages'], [])

    def test_widget_routes_known_local_operations_through_executor(self):
        self.widget.action.return_value = {'status': 'ready'}
        self.assertTrue(self.api.hud_command('widget.action', {'operation': 'timer.set', 'seconds': 30})['ok'])
        self.settle(True)
        self.widget.action.assert_called_once()
        self.assertFalse(self.api.hud_command('widget.action', {'operation': '__dict__'})['ok'])
        self.assertFalse(self.api.hud_command('widget.action', {'operation': 'timer.set', 'seconds': 0})['ok'])
        self.widget.action.reset_mock()
        self.api.hud_command('widget.action', {'operation': 'weather', 'city': 'Synthetic City'})
        reviews = self.settle(False)
        self.assertIn('widget.weather', reviews[0]['script'])
        self.widget.action.assert_not_called()

    def test_preference_validation_has_no_operating_authority(self):
        for values in ({'fps': 0}, {'particles': 501}, {'sounds_muted': 'false'}, {'accent': 'url(private)'},
                       {'sound_volume': 101}, {'allow_cloud': True}):
            with self.assertRaises((ValueError, TypeError)):
                replace(PresentationPreferences(), **values)


class DisplayTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.paths = RuntimePaths(Path(self.folder.name))
        self.paths.ensure()
        self.studio = Mock()
        self.studio._core.voice.privacy.refresh.return_value = False
        self.studio._engine.pending_review.return_value = None
        self.studio._activations.tray_available = False
        self.areas = [dict(index=0, x=0, y=0, width=1920, height=1080),
                      dict(index=1, x=-1280, y=0, width=1280, height=1024)]
        self.display = DisplayController(self.studio, self.paths, lambda: self.areas)
        self.display.window = Mock(x=20, y=20, width=1000, height=700, native=None)

    def test_mode_switches_reuse_same_window_and_geometry_is_clamped(self):
        window = self.display.window
        for mode in ('floating', 'mini', 'widget', 'fullscreen', 'window'):
            self.assertTrue(self.display.change(mode))
            self.assertIs(self.display.window, window)
        self.display.select_monitor(1)
        x, y = window.move.call_args.args
        self.assertLess(x, 0)
        self.assertGreaterEqual(x, -1280)
        self.studio._core.activate_voice.assert_not_called()
        self.assertFalse(self.display.window is None)

    def test_tray_and_compact_are_refused_without_controls_or_during_review(self):
        with self.assertRaises(PermissionDenied):
            self.display.change('tray')
        self.display.window.hide.assert_not_called()
        self.studio._activations.tray_available = True
        self.display.change('tray')
        self.display.window.hide.assert_called_once()
        self.studio._engine.pending_review.return_value = {'id': 'fixture'}
        self.display.show_review()
        self.assertEqual(self.display.mode, 'window')
        with self.assertRaises(PermissionDenied):
            self.display.change('mini')

    def test_invalid_geometry_and_unknown_modes_are_rejected(self):
        with self.assertRaises(ValueError):
            clamp_geometry({'x': True, 'y': 0, 'width': 1, 'height': 1}, self.areas[0])
        result = clamp_geometry(dict(x=99999, y=-99999, width=99999, height=99999), self.areas[0])
        self.assertEqual(result, dict(x=0, y=0, width=1920, height=1080))
        with self.assertRaises(ValueError):
            self.display.change('shell')

    def test_on_top_changes_are_marshaled_to_native_dispatcher(self):
        active, applied = [], []
        class Native:
            def Invoke(self, callback):
                active.append(True)
                try:
                    callback()
                finally:
                    active.pop()
        class Window:
            native = Native()
            @property
            def on_top(self):
                return False
            @on_top.setter
            def on_top(self, value):
                self.assert_native_thread(value)
            def assert_native_thread(self, value):
                if not active:
                    raise AssertionError('Cross-thread native property access')
                applied.append(value)
        self.display.window = Window()
        with patch('clydex.desktop.display.os.name', 'nt'), patch.dict('sys.modules', {'System': SimpleNamespace(Action=lambda f: f)}):
            self.display._set_on_top(True)
            self.display._set_on_top(False)
        self.assertEqual(applied, [True, False])

    def test_startup_restores_saved_bounds_instead_of_overwriting_with_defaults(self):
        self.display._geometry['window'] = dict(x=-1200, y=40, width=900, height=700)
        self.display.monitor = 1
        self.display.restore_geometry()
        self.display.window.move.assert_called_with(-1200, 40)
        self.display.window.resize.assert_called_with(900, 700)
