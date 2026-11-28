"""Synthetic selected workspaces, process plugins, policies and real bridge reviews."""
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
import uuid
from unittest.mock import Mock, patch

from clydex.automation.scheduler import TriggerScheduler, next_daily, validate_trigger
from clydex.automation.workflows.repository import OperatingRepository
from clydex.core.application import CoreApplication
from clydex.core.config import AppConfig, RuntimePaths
from clydex.core.contracts import ActionRequest, RequestContext
from clydex.core.errors import PermissionDenied
from clydex.database.store import LocalStore
from clydex.desktop.hud import HudBridge, HudService
from clydex.desktop.studio import Studio
from clydex.plugins.manager import PluginManager, manifest, package_snapshot
from clydex.security.permissions import PermissionService
from clydex.automation.executor import ToolExecutor
from clydex.automation.tasks import CancellationToken
from clydex.synchronization.contracts import validate_payload
from clydex.tools.developer import DeveloperTools, readonly_sql
from clydex.tools.selected import SelectedPaths
from tests.test_automation import workflow, node, edge
from tests.test_personal_data import FixtureCipher
from tests.test_regression import engine_for_test


class SelectedAndPluginTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name)
        self.selected = SelectedPaths()
        self.token = CancellationToken()

    def test_selection_rejects_traversal_absolute_links_and_expired_ids(self):
        key = self.selected.add(self.base, 'folder')
        for relative in ('../outside', str(self.base / 'arbitrary'), 'file:stream'):
            with self.assertRaises(ValueError):
                self.selected.path(key, relative, allow_missing=True)
        self.selected.clear()
        with self.assertRaises(ValueError):
            self.selected.get(key)

    def test_file_compare_and_swap_and_empty_only_folder_deletion(self):
        file = self.base / 'synthetic.txt'
        file.write_text('original', encoding='utf-8')
        key = self.selected.add(self.base, 'folder')
        args = dict(selection=key, operation='write', relative='synthetic.txt', text='changed', expected_sha256='')
        with self.assertRaises(ValueError):
            self.selected.modify(args, self.token)
        args['expected_sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
        self.selected.modify(args, self.token)
        self.assertEqual(file.read_text(encoding='utf-8'), 'changed')
        with self.assertRaises(OSError):
            self.selected.modify(dict(args, operation='delete', relative='', text='', expected_sha256=''), self.token)

    def test_git_uses_argv_disables_hooks_and_refuses_dirty_branch_switch(self):
        (self.base / '.git').mkdir()
        key = self.selected.add(self.base, 'folder')
        developer = DeveloperTools(self.selected, Mock())
        with patch('clydex.tools.developer.run_process', return_value=Mock(returncode=0, stdout=' M synthetic.txt', stderr='')) as run:
            with self.assertRaises(ValueError):
                developer.git_branch(dict(selection=key, operation='switch', branch='feature'), self.token)
            self.assertEqual(run.call_count, 1)
            args = run.call_args.args[0]
            self.assertIn('core.fsmonitor=false', args)
            self.assertFalse(run.call_args.kwargs.get('shell', False))
        for branch in ('--force', 'bad;command', '../escape'):
            with self.assertRaises(ValueError):
                developer.git_branch(dict(selection=key, operation='create', branch=branch), self.token)

    def test_sql_reader_rejects_writes_dynamic_sources_and_multiple_statements(self):
        self.assertEqual(readonly_sql('SELECT TOP 5 id FROM dbo.synthetic'), 'SELECT TOP 5 id FROM dbo.synthetic')
        for query in ('SELECT 1; DELETE FROM x', 'SELECT * INTO x FROM y', 'EXEC dangerous',
                      "SELECT * FROM OPENROWSET('x')", 'SELECT 1 -- comment', 'UPDATE x SET a=1'):
            with self.assertRaises(ValueError):
                readonly_sql(query)

    def test_plugin_manifest_refuses_permissions_dependencies_and_path_traversal(self):
        source = Path(__file__).parents[1] / 'examples/plugins/synthetic_echo'
        value = package_snapshot(source)['manifest']
        for changes in ({'entry': '../outside.py'}, {'permissions': ['shell.run']}, {'dependencies': ['unreviewed']},
                        {'version': 'latest'}, {'compatibility': 'unknown'}):
            with self.assertRaises(ValueError):
                manifest(dict(value, **changes))

    def test_actual_synthetic_plugin_is_disabled_then_hash_pinned_and_bounded(self):
        source = Path(__file__).parents[1] / 'examples/plugins/synthetic_echo'
        selected = self.selected.add(source, 'plugin')
        repo = OperatingRepository(LocalStore(self.base / 'core.sqlite'), 'synthetic', FixtureCipher())
        manager = PluginManager(self.base / 'plugins', repo, self.selected)
        candidate, key = manager.candidate(selected), str(uuid.uuid4())
        record = manager.install(selected, candidate['digest'], key)
        args = dict(plugin=key, tool='echo.text', arguments={'text': 'Synthetic SDK fixture'})
        with self.assertRaises(ValueError):
            manager.invoke(args, self.token)
        repo.save('plugin', key, dict(record['value'], enabled=True, trusted_code=True), 1)
        self.assertEqual(manager.invoke(args, self.token)['result'], {'text': 'Synthetic SDK fixture'})
        (manager.root / key / 'echo.py').write_text('# changed', encoding='utf-8')
        with self.assertRaises(ValueError):
            manager.invoke(args, self.token)

    def test_disabled_scope_rechecked_after_review(self):
        service = PermissionService()
        executor = ToolExecutor(service)
        action = ActionRequest.create('monitoring.sample', 'local', {}, RequestContext('user', 'device'))
        def review(approval, request):
            service.decide(approval, True)
            executor._disabled_scopes = frozenset({'monitoring.local'})
            return True
        effect = Mock()
        with self.assertRaises(PermissionDenied):
            executor.execute(action, effect, review, self.token)
        effect.assert_not_called()


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.repo = OperatingRepository(LocalStore(Path(self.folder.name) / 'db'), 'owner', FixtureCipher())
        self.key = str(uuid.uuid4())
        self.value = dict(name='Synthetic timer', kind='time', workflow=str(uuid.uuid4()), enabled=False,
                          source='', cooldown=60, missed='once', schedule={'timezone': 'Asia/Colombo', 'time': '08:00', 'interval_seconds': 60})
        self.repo.save('trigger', self.key, self.value, 0)

    def test_disabled_default_explicit_arming_duplicates_and_lock(self):
        submitted, allowed = [], [True]
        scheduler = TriggerScheduler(self.repo, lambda work, **kw: submitted.append(work), Mock(), lambda: allowed[0], clock=lambda: 100, start=False)
        self.assertFalse(scheduler.armed)
        with self.assertRaises(ValueError):
            scheduler.arm([self.key])
        self.repo.save('trigger', self.key, dict(self.value, enabled=True, kind='network', source='explicit-server'), 1)
        scheduler.arm([self.key])
        scheduler.event('network', 'different-server', 'e1')
        self.assertFalse(submitted)
        scheduler.event('network', 'explicit-server', 'e1')
        scheduler.event('network', 'explicit-server', 'e1')
        self.assertEqual(len(submitted), 1)
        allowed[0] = False
        scheduler.tick()
        self.assertFalse(scheduler.armed)
        submitted[0]()
        scheduler.run.assert_not_called()

    def test_timezone_daily_dst_and_invalid_bounds(self):
        from datetime import datetime, timezone
        stamp = datetime(2026, 3, 8, 6, tzinfo=timezone.utc).timestamp()
        following = next_daily({'timezone': 'America/New_York', 'time': '02:30'}, stamp)
        self.assertGreater(following - stamp, 86400 - 3600)
        with self.assertRaises(ValueError):
            validate_trigger(dict(self.value, cooldown=0))

    def test_backward_compatible_sync_rejects_grants_and_preserves_v2_data_only(self):
        value = workflow()
        self.assertEqual(validate_payload('workflows', value), value)
        value['nodes'] = [node('danger', 'tool', {'tool': 'integration.request', 'arguments': {'secret': 'not-a-real-secret'}})]
        with self.assertRaises(ValueError):
            validate_payload('workflows', value)


class OperatingBridgeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.engine = engine_for_test(AppConfig(speak_replies=False, allow_cloud=False))
        with patch('clydex.core.application.LocalCipher', FixtureCipher):
            self.core = CoreApplication(paths=RuntimePaths(Path(self.folder.name)), config=self.engine.config, engine=self.engine)
        self.addCleanup(self.core.close)
        self.studio = Studio(self.core)
        self.hud = HudService(self.studio, start=False)
        self.bridge = HudBridge(self.hud)

    def settle(self, approve=True):
        seen = []
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            pending = self.engine.pending_review()
            if pending:
                seen.append(pending)
                self.studio.decide(pending['id'], approve)
            self.hud.collect()
            if not self.core.queue.busy:
                return seen
            time.sleep(.005)
        self.core.stop()
        self.fail('Operating operation failed to settle.')

    def action(self, op, data, approve=True):
        self.assertTrue(self.bridge.hud_command('operating.action', {'operation': op, 'values': data})['ok'])
        return self.settle(approve)

    def test_real_bridge_save_enable_run_uses_single_core_and_per_action_reviews(self):
        definition = workflow([node('sample', 'tool', {'tool': 'monitoring.sample', 'arguments': {}}),
                               node('done', 'output', {'value': {'$ref': 'sample.os'}})], [edge('sample', 'done')])
        self.assertEqual(len(self.action('workflow.save', {'definition': definition, 'revision': 0})), 1)
        record = self.core.operating.repository.get('workflow', definition['id'])
        self.assertFalse(record['value']['enabled'])
        self.action('workflow.enable', {'id': record['id'], 'revision': 1, 'enabled': True})
        reviews = self.action('workflow.run', {'id': record['id'], 'inputs': {}})
        self.assertEqual(len(reviews), 1)
        self.assertIn('"source":"workflow"', reviews[0]['script'])
        history = self.core.operating.repository.history()
        self.assertEqual(history[0]['status'], 'complete')
        self.assertEqual(history[0]['nodes'], {'sample': 'complete', 'done': 'complete'})
        self.assertIs(self.hud.system, self.core.operating.system)
        self.assertEqual([x for x in dir(self.bridge) if not x.startswith('_')], ['hud_command', 'hud_read', 'hud_snapshot'])

    def test_declined_effect_leaves_failed_receipt_without_subsequent_actions(self):
        definition = workflow([node('one', 'tool', {'tool': 'monitoring.sample', 'arguments': {}}),
                               node('two', 'tool', {'tool': 'monitoring.sample', 'arguments': {}})], [edge('one', 'two')])
        self.action('workflow.save', {'definition': definition, 'revision': 0})
        self.action('workflow.enable', {'id': definition['id'], 'revision': 1, 'enabled': True})
        with patch.object(self.core.operating.system, 'sample') as sample:
            reviews = self.action('workflow.run', {'id': definition['id'], 'inputs': {}}, approve=False)
            self.assertEqual(len(reviews), 1)
            sample.assert_not_called()
        self.assertEqual(self.core.operating.repository.history()[0]['status'], 'failed')

    def test_privacy_denies_external_requests_and_lock_clears_results_and_selections(self):
        service = self.core.operating
        with self.assertRaises(PermissionDenied):
            service.external()
        service.result = {'private': 'synthetic'}
        service.capture_armed = True
        service.feeds.polling = True
        self.core.voice.privacy.probe = lambda: True
        self.core.voice.privacy.refresh()
        self.assertEqual(service.result, {})
        self.assertFalse(service.capture_armed)
        self.assertFalse(service.feeds.polling)
        self.assertFalse(self.bridge.hud_read('operating')['ok'])

    def test_unknown_tools_and_arbitrary_bridge_paths_cannot_execute(self):
        self.assertFalse(self.bridge.hud_command('operating.select', {'kind': 'file', 'path': 'arbitrary'})['ok'])
        self.action('tool.invoke', {'tool': 'shell.run', 'arguments': {'script': 'arbitrary'}})
        self.assertIn('failed', self.core.operating.error)
        self.assertEqual(self.core.operating.repository.history(), [])

    def test_capture_requires_optin_and_native_indicator_before_worker(self):
        with patch('clydex.automation.workspace.worker') as capture:
            self.action('tool.invoke', {'tool': 'capture.once', 'arguments': {'kind': 'screen', 'device': 0}})
            capture.assert_not_called()
            self.action('capture.arm', {'enabled': True})
            self.core.operating.capture_indicator = lambda active: False
            self.action('tool.invoke', {'tool': 'capture.once', 'arguments': {'kind': 'screen', 'device': 0}})
            capture.assert_not_called()
            self.core.operating.capture_indicator = Mock(return_value=True)
            capture.return_value = {'image': 'synthetic-frame-placeholder', 'width': 1, 'height': 1}
            self.action('tool.invoke', {'tool': 'capture.once', 'arguments': {'kind': 'screen', 'device': 0}})
            capture.assert_called_once()
            self.assertGreater(self.core.operating.capture_expires, time.monotonic())
            self.core.stop()
            self.assertFalse(self.core.operating.capture_armed)
            self.assertEqual(self.core.operating.result, {})

    def test_credential_review_contains_digest_and_never_retrieves_secret_to_hud(self):
        key = str(uuid.uuid4())
        value = dict(name='Synthetic diagnostics', kind='windows', enabled=False)
        self.action('profile.save', {'id': key, 'revision': 0, 'value': value})
        self.core.credentials = Mock()
        self.core.credentials.set.return_value = None
        secret = 'synthetic-credential-for-test-only'
        reviews = self.action('credential.set', {'id': key, 'secret': secret})
        self.assertNotIn(secret, reviews[0]['script'])
        self.assertIn(hashlib.sha256(secret.encode()).hexdigest(), reviews[0]['script'])
        self.core.credentials.set.assert_called_once_with('operating.' + key, secret)
        self.assertNotIn(secret, json.dumps(self.core.operating.snapshot()))

    def test_feed_cannot_poll_modifying_service_operation(self):
        service, key, feed = self.core.operating, str(uuid.uuid4()), str(uuid.uuid4())
        service.repository.save('integration', key, dict(name='Synthetic GitHub', service='github',
            endpoint='https://api.github.com', resource='synthetic/repo', version='', enabled=True), 0)
        service.repository.save('feed', feed, dict(name='Unsafe feed', kind='github', profile=key,
            operation='create_issue', enabled=True, interval=60, threshold=85, cooldown=60), 0)
        with patch.object(service.integrations, 'request') as request:
            self.action('feed.refresh', {'id': feed})
            request.assert_not_called()
        self.assertEqual(service.feeds.results[feed]['status'], 'failed')

    def test_received_cloud_tombstone_disables_imported_workflow_before_run(self):
        definition = workflow()
        remote_id, binding = str(uuid.uuid4()), 'synthetic-binding'
        self.core.cloud.binding = binding
        self.core.operating.repository.save('workflow', definition['id'], dict(definition=definition,
            enabled=True, origin='cloud_import', remote_id=remote_id, binding=binding), 0)
        with self.core.store.connect() as connection:
            connection.execute('INSERT INTO sync_replicas VALUES(?,?,?,?,?,?,?)',
                (self.core.operating.owner, binding, 'workflows', remote_id, None, 2, 1))
        self.action('workflow.run', {'id': definition['id'], 'inputs': {}})
        self.assertFalse(self.core.operating.repository.get('workflow', definition['id'])['value']['enabled'])
        self.assertEqual(self.core.operating.repository.history(), [])
