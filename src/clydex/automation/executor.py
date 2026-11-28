"""Every adapter effect crosses a fixed policy and exact-action review boundary."""
import time
from typing import Callable

from clydex.automation.tasks import CancellationToken
from clydex.core.contracts import ActionRequest, Risk, ToolOperation
from clydex.core.errors import Cancelled, PermissionDenied
from clydex.security.permissions import Approval, PermissionService, TOOL_SPECS


class ToolExecutor:
    def __init__(self, permissions: PermissionService, audit: Callable | None = None,
                 disabled_scopes: tuple[str, ...] = ()):
        self.permissions = permissions
        self._audit = audit or (lambda *args: None)
        self._specs = {spec.name: spec for spec in TOOL_SPECS}
        self._disabled_scopes = frozenset(disabled_scopes)

    def execute(self, action: ActionRequest, operation: ToolOperation,
                review: Callable[[Approval, ActionRequest], bool], token: CancellationToken,
                *, explicit_cloud_request: bool = False):
        spec = self._specs.get(action.tool)
        if spec is None:
            self._audit(action.digest, 'unknown', 'denied')
            raise PermissionDenied('Unknown tool.')
        if spec.scope in self._disabled_scopes:
            self._audit(action.digest, action.tool, 'denied')
            raise PermissionDenied('This capability is disabled by local policy.')
        try:
            spec.validate(action.arguments)
        except ValueError:
            self._audit(action.digest, action.tool, 'denied')
            raise
        # Closing a window can lose unsaved changes; other layout operations are low risk.
        low_manage = action.tool == 'app.manage' and action.arguments['operation'] != 'close'
        low = (spec.risk == Risk.LOW and (action.tool != 'app.manage' or low_manage)
               and action.context.source == 'user')
        # A user-entered question with no private/history/tool context is an explicit Codex request.
        direct_cloud = (action.tool == 'provider.codex' and explicit_cloud_request
                        and action.context.source == 'user')
        token.check()
        self._audit(action.digest, action.tool, 'requested')
        if not (low or direct_cloud):
            approval = self.permissions.issue(action)
            try:
                if not review(approval, action):
                    token.check()
                    raise PermissionDenied('Action was not approved.')
                token.check()
                self.permissions.consume(approval, action)
            except Cancelled:
                self._audit(action.digest, action.tool, 'cancelled')
                raise
            except PermissionDenied:
                self._audit(action.digest, action.tool, 'denied')
                raise
            finally:
                self.permissions.revoke(approval)
        token.check()
        if spec.scope in self._disabled_scopes:
            self._audit(action.digest, action.tool, 'denied')
            raise PermissionDenied('Capability was disabled while awaiting approval.')
        self._audit(action.digest, action.tool, 'approved')
        started = time.monotonic()
        try:
            result = operation(action.arguments)
            try:
                spec.validate_result(result)
            except ValueError:
                raise RuntimeError('Tool result violated its contract; effects may have completed.')
            # Never retry a non-idempotent operation after timeout or cancellation.
            # Native adapters must implement their own cooperative timeout/stop.
            if time.monotonic() - started > spec.timeout:
                raise RuntimeError('Tool exceeded its time budget; effects may have completed.')
            token.check()
        except Cancelled:
            self._audit(action.digest, action.tool, 'cancelled')
            raise
        except Exception:
            self._audit(action.digest, action.tool, 'failed')
            raise
        self._audit(action.digest, action.tool, 'executed')
        return result
