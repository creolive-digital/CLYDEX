"""One-time, action-bound consent. Only the trusted local bridge may decide reviews."""
from dataclasses import dataclass, replace
import threading
import time
from typing import Callable
import uuid

from clydex.core.contracts import ActionRequest, Risk, ToolSpec
from clydex.core.errors import PermissionDenied
from clydex.providers.base import PROVIDER_IDS
from clydex.tools.catalog import OPERATING_SPECS


@dataclass(frozen=True)
class Approval:
    id: str
    digest: str
    user_id: str
    device_id: str
    expires_at: float


class PermissionService:
    """In-memory authority, never model output or a persisted reusable capability.

    This boundary supervises trusted Python adapters; it is not a sandbox for
    arbitrary code running under the same Windows user.
    """

    def __init__(self, timeout: float = 120, clock: Callable[[], float] = time.monotonic):
        if not 0 < timeout <= 900:
            raise ValueError('Invalid approval lifetime.')
        self.timeout = timeout
        self.clock = clock
        self._lock = threading.Lock()
        self._pending: dict[str, tuple[Approval, bool | None]] = {}

    def issue(self, action: ActionRequest) -> Approval:
        with self._lock:
            self._pending = {key: pair for key, pair in self._pending.items()
                             if pair[0].expires_at > self.clock()}
            if len(self._pending) >= 64:
                raise PermissionDenied('Too many pending approvals.')
            approval = Approval(uuid.uuid4().hex, action.digest, action.context.user_id,
                                action.context.device_id, self.clock() + self.timeout)
            self._pending[approval.id] = approval, None
            return approval

    def decide(self, approval: Approval, approve: bool) -> bool:
        with self._lock:
            pair = self._pending.get(approval.id)
            if (type(approve) is not bool or pair is None or pair[0] != approval
                    or pair[1] is not None or approval.expires_at <= self.clock()):
                return False
            self._pending[approval.id] = approval, approve
            return True

    def consume(self, approval: Approval, action: ActionRequest) -> None:
        with self._lock:
            pair = self._pending.pop(approval.id, None)
            if (pair is None or pair != (approval, True) or approval.expires_at <= self.clock()
                    or approval.digest != action.digest or approval.user_id != action.context.user_id
                    or approval.device_id != action.context.device_id):
                raise PermissionDenied('Approval is absent, expired, changed or already consumed.')

    def revoke(self, approval: Approval) -> None:
        with self._lock:
            self._pending.pop(approval.id, None)

    def revoke_all(self) -> None:
        with self._lock:
            self._pending.clear()


# No model-controlled risk/scope fields. Only these installed capabilities exist.
TOOL_SPECS = (
    ToolSpec('cloud.configure', 'cloud.settings', Risk.HIGH, 30, (('configuration', dict),), (dict,)),
    ToolSpec('cloud.request', 'cloud.vault', Risk.HIGH, 900,
             (('operation', str), ('destination', str), ('data', dict), ('credential_digest', str)), (dict,)),
    ToolSpec('sync.apply', 'local.synchronization', Risk.HIGH, 120, (('change', dict),), (dict,)),
    ToolSpec('knowledge.cache', 'local.knowledge', Risk.HIGH, 120, (('operation', str), ('data', dict)), (dict,)),
    ToolSpec('app.launch', 'apps.launch', Risk.LOW, 25, (('name', str), ('app_id', str)), (type(None),)),
    ToolSpec('app.read', 'apps.inspect', Risk.SENSITIVE, 25, (('action', str), ('target', str)), (list,)),
    ToolSpec('app.manage', 'apps.windows', Risk.LOW, 10, (('operation', str), ('window', dict)), (str,)),
    ToolSpec('app.interact', 'apps.modify', Risk.HIGH, 25,
             (('operation', str), ('window', dict), ('control', dict), ('text', str)), (bool,)),
    ToolSpec('browser.read', 'browser.visible', Risk.SENSITIVE, 70,
             (('target', str), ('channel', str), ('existing', bool)), (dict,)),
    ToolSpec('mail.read', 'mail.inbox', Risk.SENSITIVE, 180, (('unread', bool),), (list,)),
    ToolSpec('mail.draft', 'mail.drafts', Risk.HIGH, 180,
             (('number', int), ('body', str), ('message_key', list)), (str,)),
    ToolSpec('shell.run', 'shell.powershell', Risk.HIGH, 120, (('script', str),), (dict,)),
    ToolSpec('provider.health', 'providers.health', Risk.SENSITIVE, 30, (('configuration', str),), (str,)),
    ToolSpec('provider.configure', 'providers.settings', Risk.HIGH, 30,
             (('name', str), ('configuration', str), ('credential_digest', str), ('remove_key', bool)), (dict,)),
    ToolSpec('voice.configure', 'voice.settings', Risk.HIGH, 120,
             (('configuration', str), ('artifacts', dict)), (dict,)),
    ToolSpec('voice.download', 'voice.models', Risk.HIGH, 900,
             (('model', str), ('directory', str)), (dict,)),
    ToolSpec('voice.arm', 'voice.microphone', Risk.SENSITIVE, 120, (('configuration', str),), (dict,)),
    ToolSpec('personality.configure', 'presentation.settings', Risk.HIGH, 30,
             (('configuration', str), ('address', str)), (dict,)),
    ToolSpec('desktop.configure', 'desktop.settings', Risk.HIGH, 30, (('values', dict),), (dict,)),
    ToolSpec('permissions.configure', 'security.settings', Risk.HIGH, 30, (('disabled_scopes', list),), (dict,)),
    ToolSpec('widget.control', 'desktop.time_tools', Risk.LOW, 30, (('values', dict),), (dict,)),
    ToolSpec('widget.weather', 'desktop.weather', Risk.SENSITIVE, 60, (('values', dict),), (dict,)),
    ToolSpec('conversation.manage', 'local.history', Risk.HIGH, 30,
             (('operation', str), ('id', str), ('title', str), ('persistent', bool), ('days', int)), (dict,)),
    ToolSpec('memory.manage', 'local.memory', Risk.HIGH, 30,
             (('operation', str), ('id', str), ('category', str), ('value', str), ('local_only', bool),
              ('revision', int), ('origin', str), ('source_id', str), ('source_kind', str)), (dict,)),
    ToolSpec('memory.configure', 'local.memory.policy', Risk.HIGH, 30,
             (('enabled', bool), ('automatic', bool), ('categories', list)), (dict,)),
)
TOOL_SPECS += tuple(ToolSpec('provider.' + name, 'cloud.' + name if name != 'ollama' else 'local.ollama',
    Risk.SENSITIVE, 900, (('instructions', str), ('data', dict), ('schema', dict), ('fast', bool),
                         ('configuration', str), ('attempt', int)), (dict,)) for name in PROVIDER_IDS)

TOOL_SPECS += OPERATING_SPECS

# Annotate legacy installed adapters without changing their established approval behavior.
TOOL_SPECS = tuple(replace(s,
    platforms=('Windows',) if s.name.startswith(('app.', 'browser.', 'mail.', 'shell.', 'voice.', 'desktop.', 'widget.')) else s.platforms,
    read_only=s.read_only or s.name in ('app.read', 'browser.read', 'mail.read', 'provider.health'),
    idempotent=s.idempotent or s.name in ('app.read', 'browser.read', 'mail.read'),
    destinations=(s.name.removeprefix('provider.') + ' configured endpoint',) if s.name.startswith('provider.')
        and s.name not in ('provider.configure', 'provider.health') else s.destinations)
    for s in TOOL_SPECS)
