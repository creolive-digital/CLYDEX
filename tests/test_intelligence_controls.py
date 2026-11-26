"""Functional bridge controls and real permission reviews, with isolated user data."""
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from clydex.core.application import CoreApplication
from clydex.core.config import RuntimePaths
from clydex.desktop.studio import Studio
from tests.test_intelligence import Credentials
from tests.test_personal_data import FixtureCipher
from tests.test_regression import engine_for_test


class ControlsTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.engine = engine_for_test()
        with patch('clydex.core.application.CredentialStore', Credentials), patch(
                'clydex.core.application.LocalCipher', FixtureCipher):
            self.core = CoreApplication(paths=RuntimePaths(Path(self.folder.name)), engine=self.engine)
        self.addCleanup(self.core.close)
        self.studio = Studio(self.core)

    def settle(self, approve=True):
        events, reviews = [], []
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            snapshot = self.studio.snapshot()
            events.extend(snapshot['intelligence_events'])
            if snapshot['review']:
                reviews.append(snapshot['review'])
                self.studio.decide(snapshot['review']['id'], approve)
            if not snapshot['busy']:
                return events, reviews
            time.sleep(.005)
        self.studio.stop()
        self.fail('Desktop operation did not settle.')

    def test_provider_secret_stays_out_of_review_settings_and_events(self):
        self.assertTrue(self.studio.configure_provider('openai', {'model': 'fixture-model'}, 'synthetic-key'))
        events, reviews = self.settle()
        self.assertEqual(len(reviews), 1)
        self.assertNotIn('synthetic-key', repr(events) + repr(reviews) + repr(self.studio.intelligence_settings()))
        self.assertEqual(self.core.credentials.get('provider.openai'), 'synthetic-key')
        self.assertFalse(self.core.providers.configs['openai'].enabled)

    def test_provider_configuration_denial_changes_nothing(self):
        self.studio.configure_provider('openai', {'model': 'fixture-model'}, 'synthetic-key')
        self.settle(approve=False)
        self.assertEqual(self.core.providers.configs['openai'].model, '')
        self.assertIsNone(self.core.credentials.get('provider.openai'))

    def test_mutating_controls_respect_queue_and_approval(self):
        self.studio.conversation_action({'operation': 'new', 'title': 'Synthetic session', 'persistent': True})
        self.assertFalse(self.studio.configure_routing({'privacy': True}))
        self.assertFalse(self.studio.resume_conversation('invalid'))
        self.assertEqual(self.studio.intelligence_settings(), {'busy': True})
        _, reviews = self.settle()
        self.assertIn('conversation.manage', reviews[0]['script'])
        key = self.core.conversations.current.id
        self.assertFalse(self.core.conversations.current.temporary)
        self.core.conversations.record('synthetic question', 'synthetic answer')
        self.studio.conversation_action({'operation': 'new', 'title': 'Temporary', 'persistent': False})
        self.settle()
        self.studio.resume_conversation(key)
        events, _ = self.settle()
        self.assertTrue(any('transcript' in data for kind, data in events if kind == 'intelligence_result'))
        self.assertEqual(self.engine.history[0], ('User', 'synthetic question'))
        self.assertIn('synthetic answer', self.studio.export_conversation(key))

    def test_memory_controls_policy_and_provenance(self):
        self.studio.memory_action({'operation': 'add', 'category': 'facts', 'value': 'Synthetic fact'})
        _, reviews = self.settle()
        self.assertIn('memory.manage', reviews[0]['script'])
        record = self.studio.memories()['records'][0]
        self.assertEqual(record['source_kind'], 'manual_ui')
        self.assertTrue(record['local_only'])
        self.studio.configure_memory({'enabled': False, 'automatic': False, 'categories': []})
        self.settle()
        self.assertFalse(self.studio.memories()['policy']['enabled'])
        self.studio.memory_action({'operation': 'delete', 'id': record['id']})
        self.settle()
        self.assertEqual(self.studio.memories()['records'], [])

    def test_routing_privacy_control_does_not_contact_providers(self):
        self.studio.configure_routing({'privacy': True, 'offline': True})
        _, reviews = self.settle()
        self.assertTrue(self.core.providers.routing.privacy)
        self.assertTrue(self.core.providers.routing.offline)
        self.assertIn('provider.configure', reviews[0]['script'])
        self.engine.provider.respond.assert_not_called()
