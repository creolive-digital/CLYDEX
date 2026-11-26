from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import unittest
from unittest.mock import Mock

from clydex.automation.executor import ToolExecutor
from clydex.automation.tasks import CancellationToken
from clydex.core.contracts import ActionRequest, RequestContext
from clydex.core.errors import Cancelled, PermissionDenied
from clydex.security.permissions import PermissionService


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.now = 10.0
        self.permissions = PermissionService(5, lambda: self.now)
        self.context = RequestContext('user', 'device', 'request')
        self.action = ActionRequest.create('shell.run', 'profile', {'script': 'approved text'}, self.context)

    def approve(self, approval, action):
        return self.permissions.decide(approval, True)

    def test_approval_consumed_only_once(self):
        approval = self.permissions.issue(self.action)
        self.assertTrue(self.permissions.decide(approval, True))
        self.permissions.consume(approval, self.action)
        with self.assertRaises(PermissionDenied):
            self.permissions.consume(approval, self.action)

    def test_changed_arguments_target_tool_request_and_identity_denied(self):
        changed = [replace(self.action, target='other'), replace(self.action, tool='mail.draft'),
                   replace(self.action, arguments_json='{"script":"changed"}'),
                   replace(self.action, context=replace(self.context, user_id='other')),
                   replace(self.action, context=replace(self.context, device_id='other')),
                   replace(self.action, context=replace(self.context, request_id='other')),
                   replace(self.action, context=replace(self.context, source='plugin'))]
        for action in changed:
            with self.subTest(action=action):
                approval = self.permissions.issue(self.action)
                self.permissions.decide(approval, True)
                with self.assertRaises(PermissionDenied):
                    self.permissions.consume(approval, action)

    def test_expiry_at_exact_deadline(self):
        approval = self.permissions.issue(self.action)
        self.permissions.decide(approval, True)
        self.now = 15
        with self.assertRaises(PermissionDenied):
            self.permissions.consume(approval, self.action)

    def test_decline_unknown_and_duplicate_decision(self):
        approval = self.permissions.issue(self.action)
        self.assertFalse(self.permissions.decide(approval, 'true'))
        self.assertTrue(self.permissions.decide(approval, False))
        self.assertFalse(self.permissions.decide(approval, True))
        with self.assertRaises(PermissionDenied):
            self.permissions.consume(approval, self.action)

    def test_revocation_invalidates_pending_grants(self):
        approval = self.permissions.issue(self.action)
        self.permissions.decide(approval, True)
        self.permissions.revoke_all()
        with self.assertRaises(PermissionDenied):
            self.permissions.consume(approval, self.action)

    def test_racing_consumers_execute_at_most_once(self):
        approval = self.permissions.issue(self.action)
        self.permissions.decide(approval, True)
        def consume(_):
            try:
                self.permissions.consume(approval, self.action)
                return 1
            except PermissionDenied:
                return 0
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(consume, range(20))), 1)

    def test_denial_cannot_reach_operation(self):
        operation = Mock()
        executor = ToolExecutor(self.permissions)
        with self.assertRaises(PermissionDenied):
            executor.execute(self.action, operation, lambda *_: False, CancellationToken())
        operation.assert_not_called()

    def test_disabled_scope_cannot_be_overridden_by_approval(self):
        operation, review = Mock(), Mock()
        with self.assertRaises(PermissionDenied):
            ToolExecutor(self.permissions, disabled_scopes=('shell.powershell',)).execute(
                self.action, operation, review, CancellationToken())
        operation.assert_not_called()
        review.assert_not_called()

    def test_cancel_after_approval_cannot_reach_operation(self):
        operation = Mock()
        token = CancellationToken()
        def approve(approval, action):
            self.permissions.decide(approval, True)
            token.set()
            return True
        with self.assertRaises(Cancelled):
            ToolExecutor(self.permissions).execute(self.action, operation, approve, token)
        operation.assert_not_called()

    def test_review_true_without_authority_cannot_execute(self):
        operation = Mock()
        with self.assertRaises(PermissionDenied):
            ToolExecutor(self.permissions).execute(self.action, operation, lambda *_: True, CancellationToken())
        operation.assert_not_called()

    def test_unknown_tool_and_model_supplied_scope_are_rejected(self):
        operation = Mock()
        for action in (replace(self.action, tool='root.shell'),
                       replace(self.action, arguments_json='{"script":"ok","risk":"low"}')):
            with self.subTest(action=action), self.assertRaises((ValueError, PermissionDenied)):
                ToolExecutor(self.permissions).execute(action, operation, self.approve, CancellationToken())
        operation.assert_not_called()

    def test_model_low_risk_action_still_needs_user_review(self):
        action = ActionRequest.create('app.launch', 'Notepad', {'name': 'Notepad', 'app_id': 'notepad'},
                                      replace(self.context, source='model'))
        operation = Mock()
        with self.assertRaises(PermissionDenied):
            ToolExecutor(self.permissions).execute(action, operation, lambda *_: False, CancellationToken())
        operation.assert_not_called()

    def test_deterministic_explicit_app_launch_runs_without_extra_review(self):
        action = ActionRequest.create('app.launch', 'Notepad', {'name': 'Notepad', 'app_id': 'notepad'},
                                      self.context)
        operation = Mock(return_value=None)
        self.assertEqual(ToolExecutor(self.permissions).execute(action, operation, Mock(), CancellationToken()),
                         None)

    def test_window_close_always_requires_approval(self):
        action = ActionRequest.create('app.manage', 'Notepad', {'operation': 'close', 'window': {}},
                                      self.context)
        operation = Mock(return_value='closed')
        with self.assertRaises(PermissionDenied):
            ToolExecutor(self.permissions).execute(action, operation, lambda *_: False, CancellationToken())
        operation.assert_not_called()

    def test_audit_failure_prevents_effect_and_effect_is_not_retried(self):
        operation = Mock()
        with self.assertRaises(OSError):
            ToolExecutor(self.permissions, Mock(side_effect=OSError('disk full'))).execute(
                self.action, operation, self.approve, CancellationToken())
        operation.assert_not_called()
        operation.side_effect = RuntimeError('partial effect')
        with self.assertRaises(RuntimeError):
            ToolExecutor(self.permissions).execute(self.action, operation, self.approve, CancellationToken())
        self.assertEqual(operation.call_count, 1)
