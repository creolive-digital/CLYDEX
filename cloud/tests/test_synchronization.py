"""Conflict/privacy/tombstone guarantees against simulated SQL storage."""
from copy import deepcopy
import uuid
import unittest

from clydex_cloud.authentication.service import Principal
from clydex_cloud.core.errors import CloudError
from clydex_cloud.synchronization.service import Synchronization
from clydex.synchronization.contracts import CATEGORIES, validate_payload
import test_security


class SynchronizationTests(unittest.TestCase):
    def setUp(self):
        test_security.SecurityTests.setUp(self)
        self.sync = Synchronization(self.db, self.cipher, self.auth)
        self.sync.configure(self.actor, {c: c == 'memory' for c in CATEGORIES})
        self.operation = dict(operation_id=str(uuid.uuid4()), entity_id=str(uuid.uuid4()), category='memory',
            base_version=0, deleted=False, payload=dict(category='preferences', value='Synthetic cyan preference',
                local_only=False, confirmed=True, origin='explicit', source_kind='manual_ui'))

    def test_duplicate_request_is_same_result_and_digest_change_conflicts(self):
        first = self.sync.push(self.actor, [self.operation])
        self.assertEqual(first, self.sync.push(self.actor, [self.operation]))
        self.assertEqual(len(self.sync.pull(self.actor)['changes']), 1)
        changed = deepcopy(self.operation)
        changed['payload']['value'] = 'Changed synthetic request'
        with self.assertRaises(CloudError) as conflict:
            self.sync.push(self.actor, [changed])
        self.assertEqual(conflict.exception.code, 'idempotency_mismatch')

    def test_conflict_and_deletion_cannot_resurrect_from_stale_offline_client(self):
        self.sync.push(self.actor, [self.operation])
        deleted = dict(self.operation, operation_id=str(uuid.uuid4()), base_version=1, deleted=True, payload={})
        self.sync.push(self.actor, [deleted])
        stale = dict(self.operation, operation_id=str(uuid.uuid4()))
        with self.assertRaises(CloudError) as conflict:
            self.sync.push(self.actor, [stale])
        self.assertEqual(conflict.exception.metadata['current_version'], 2)
        changes = self.sync.pull(self.actor, cursor=0, limit=1)
        self.assertTrue(changes['has_more'])
        self.assertEqual(changes['changes'][0]['payload'], {})
        self.assertTrue(changes['changes'][0]['deleted'])
        next_page = self.sync.pull(self.actor, cursor=changes['cursor'])
        self.assertEqual(next_page['changes'][0]['payload'], {})
        self.assertTrue(next_page['changes'][0]['deleted'])

    def test_cross_account_isolation_and_disabled_category(self):
        self.sync.push(self.actor, [self.operation])
        second = self.auth.provision('another-fixture', 'Another-Local-Fixture-73')
        actor = Principal(second['account_id'], str(uuid.uuid4()), None, self.actor.scopes)
        self.assertEqual(self.sync.pull(actor)['changes'], [])
        with self.assertRaises(CloudError):
            self.sync.push(actor, [self.operation])

    def test_local_only_temporary_sensitive_and_permission_payloads_rejected(self):
        memory = deepcopy(self.operation)
        memory['payload']['local_only'] = True
        with self.assertRaises(CloudError):
            self.sync.push(self.actor, [memory])
        for category, value in [('preferences', {'microphone_enabled': True}),
                ('history', {'title': 'fixture', 'messages': [], 'temporary': True, 'local_only': False, 'sensitive': False}),
                ('devices', {'display_name': 'fixture', 'platform': 'Windows', 'scopes': ['shell.run']}),
                ('themes', {'startup_greeting': True}),
                ('workflows', {'contract_version': 1, 'name': 'fixture', 'nodes': [{'kind': 'shell', 'script': 'never'}], 'edges': []})]:
            with self.assertRaises(ValueError):
                validate_payload(category, value)

    def test_batch_rolls_back_prior_operation_if_later_operation_conflicts(self):
        invalid = dict(self.operation, operation_id=str(uuid.uuid4()), entity_id=str(uuid.uuid4()), base_version=999)
        with self.assertRaises(CloudError):
            self.sync.push(self.actor, [self.operation, invalid])
        self.assertEqual(self.sync.pull(self.actor)['changes'], [])
