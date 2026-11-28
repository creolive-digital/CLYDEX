"""Synthetic workflow/security contracts; no operating or external effects."""
import copy
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import Mock

from clydex.automation.tasks import CancellationToken
from clydex.automation.workflows.repository import OperatingRepository
from clydex.automation.workflows.runtime import WorkflowRuntime
from clydex.automation.workflows.schema import validate_workflow
from clydex.core.contracts import Risk, ToolSpec
from clydex.core.errors import Cancelled
from clydex.database.store import LocalStore
from clydex.security.schema import validate
from tests.test_personal_data import FixtureCipher


def workflow(nodes=None, edges=None):
    return dict(contract_version=2, id=str(uuid.uuid4()), name='Synthetic workflow', timeout=30,
                inputs={'type': 'object', 'properties': {}, 'required': [], 'additionalProperties': False},
                nodes=nodes or [node('start', 'input', {})], edges=edges or [])


def node(key, kind, config):
    return dict(id=key, kind=kind, config=config, x=10, y=10)


def edge(a, b, port='next'):
    return {'from': a, 'to': b, 'port': port}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.specs = {'fixture': ToolSpec('fixture', 'fixture', Risk.HIGH, 5, (('value', int),), (dict,))}
        self.invoke = Mock(return_value={'observed': 7})
        self.runtime = WorkflowRuntime(self.specs, self.invoke, Mock(), Mock())

    def test_schema_rejects_bool_integer_unknown_fields_refs_and_nan(self):
        for value, schema in [(True, {'type': 'integer'}), ({'extra': 1}, {'type': 'object'}),
                              (1, {'$ref': 'https://invalid.test/schema'}), (float('nan'), {'type': 'number'})]:
            with self.assertRaises(ValueError):
                validate(value, schema)

    def test_cycle_unknown_tool_and_budget_rejected_without_effect(self):
        cases = [workflow([node('a', 'input', {}), node('b', 'input', {})], [edge('a', 'b'), edge('b', 'a')]),
                 workflow([node('a', 'tool', {'tool': 'unknown', 'arguments': {}})]),
                 workflow([node('a', 'loop', {'count': 11, 'tool': 'fixture', 'arguments': {'value': 1}})])]
        for value in cases:
            with self.assertRaises(ValueError):
                self.runtime.preview(value)
        self.invoke.assert_not_called()

    def test_branching_output_and_preview_never_executes(self):
        value = workflow([node('check', 'condition', {'left': 2, 'operator': 'gt', 'right': 1}),
                          node('yes', 'tool', {'tool': 'fixture', 'arguments': {'value': 1}}),
                          node('no', 'tool', {'tool': 'fixture', 'arguments': {'value': 2}}),
                          node('result', 'output', {'value': {'$ref': 'yes.observed'}})],
                         [edge('check', 'yes', 'true'), edge('check', 'no', 'false'), edge('yes', 'result')])
        self.assertEqual(self.runtime.preview(value)['effects_executed'], 0)
        self.invoke.assert_not_called()
        result = self.runtime.run(value, {}, CancellationToken())
        self.assertEqual(result['outputs'], {'result': 7})
        self.assertEqual(result['nodes']['no'], 'skipped')
        self.assertEqual(self.invoke.call_count, 1)

    def test_loop_cancellation_prevents_subsequent_effects(self):
        token = CancellationToken()
        self.invoke.side_effect = lambda *a: token.set()
        value = workflow([node('a', 'loop', {'count': 5, 'tool': 'fixture', 'arguments': {'value': 1}})])
        with self.assertRaises(Cancelled):
            self.runtime.run(value, {}, token)
        self.assertEqual(self.invoke.call_count, 1)

    def test_forward_reference_and_permission_fields_rejected(self):
        value = workflow([node('a', 'tool', {'tool': 'fixture', 'arguments': {'value': {'$ref': 'b'}}}),
                          node('b', 'input', {})])
        with self.assertRaises(ValueError):
            validate_workflow(value)
        value = workflow()
        value['permissions'] = ['everything']
        with self.assertRaises(ValueError):
            validate_workflow(value)

    def test_repository_versions_cas_owner_binding_and_interrupted_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            store = LocalStore(Path(folder) / 'fixture.sqlite3')
            repo = OperatingRepository(store, 'fixture-owner', FixtureCipher())
            definition = workflow()
            key = definition['id']
            record = {'definition': definition, 'enabled': False}
            repo.save('workflow', key, record, 0)
            with self.assertRaises(ValueError):
                repo.save('workflow', key, record, 0)
            changed = copy.deepcopy(record)
            changed['definition']['name'] = 'Updated fixture'
            repo.save('workflow', key, changed, 1)
            self.assertEqual(len(repo.versions(key)), 2)
            with self.assertRaises(ValueError):
                OperatingRepository(store, 'other-owner', FixtureCipher()).get('workflow', key)
            repo.start_run(key, 2)
            reopened = OperatingRepository(store, 'fixture-owner', FixtureCipher())
            self.assertEqual(reopened.history()[0]['status'], 'interrupted')
            self.assertNotIn('Updated fixture'.encode(), store.path.read_bytes())

    def test_event_duplicate_claim_and_expiry(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = OperatingRepository(LocalStore(Path(folder) / 'db'), 'owner', FixtureCipher())
            key = str(uuid.uuid4())
            self.assertTrue(repo.claim_event(key, 'a' * 64, 1, ttl=10))
            self.assertFalse(repo.claim_event(key, 'a' * 64, 2))
            self.assertTrue(repo.claim_event(key, 'a' * 64, 12))
