"""Local desktop controls backed by the existing supervised Core queue."""
from dataclasses import asdict, replace
import getpass
import hashlib

from clydex.core.contracts import RequestContext, canonical_json
from clydex.core.orchestrator import IntelligenceCoordinator
from clydex.providers.registry import RoutingConfig


class IntelligenceControls:
    def _intelligence_work(self, operation):
        def perform():
            self._engine._request_context = RequestContext(getpass.getuser(), 'local-desktop')
            try:
                result = operation()
                self._engine.events.put(('intelligence_result', result))
            finally:
                self._engine.events.put(('done', None))
        return self._start('REVIEWING SETTINGS', perform)

    def intelligence_settings(self):
        with self._lock:
            if self._core.voice.privacy.refresh():
                return {'locked': True}
            if self._busy:
                return {'busy': True}
            return dict(self._core.providers.snapshot(), memory_policy=self._core.memory.policy(),
                        current=asdict(self._core.conversations.current),
                        privacy_ceiling=self._core.config.privacy_mode,
                        cloud_allowed=self._core.config.allow_cloud)

    def configure_provider(self, name, values, secret=None, remove_key=False):
        with self._lock:
            if self._busy:
                return False
            if type(remove_key) is not bool or not isinstance(values, dict) or 'id' in values:
                raise ValueError('Invalid settings.')
            config = replace(self._core.providers.configs[name], **values)
            values = config.public_dict()
            values.pop('id')
            if secret is not None and (not isinstance(secret, str) or not secret.isascii()
                    or not 1 <= len(secret) <= 1280 or any(c.isspace() for c in secret)):
                raise ValueError('Invalid credential token.')
            args = dict(name=name, configuration=canonical_json(config.public_dict()),
                        credential_digest=hashlib.sha256(secret.encode()).hexdigest() if secret else '',
                        remove_key=remove_key)
            def apply(a):
                self._core.providers.configure(a['name'], values, secret, a['remove_key'])
                return {'refresh': True}
            return self._intelligence_work(lambda: self._engine.execute_tool('provider.configure', name, args,
                apply, 'Save this provider configuration? Credentials go only to Windows Credential Manager. '
                'Enabling a cloud provider permits requests only after outbound policy and request review.'))

    def configure_routing(self, values):
        with self._lock:
            if self._busy:
                return False
            if not isinstance(values, dict):
                raise ValueError('Invalid routing settings.')
            config = replace(self._core.providers.routing, **values)
            assert isinstance(config, RoutingConfig)
            values = asdict(config)
            encoded = canonical_json(asdict(config))
            def apply(_):
                self._core.providers.configure_routing(values)
                return {'refresh': True}
            return self._intelligence_work(lambda: self._engine.execute_tool('provider.configure', 'routing',
                dict(name='routing', configuration=encoded, credential_digest='', remove_key=False), apply,
                'Save routing priorities, privacy/offline policy and explicit fallback choices?'))

    def check_provider(self, name):
        with self._lock:
            return self._intelligence_work(lambda: {'connection_status':
                IntelligenceCoordinator(self._core.providers).check_provider(self._engine, name), 'refresh': True})

    def conversations(self, query=''):
        with self._lock:
            return [] if self._busy or self._core.voice.privacy.refresh() else self._core.conversations.repository.list(query)

    def resume_conversation(self, key):
        with self._lock:
            if self._busy:
                return False
            def resume():
                records = self._core.conversations.resume(key)
                self._core.data_actions.reset_context()
                # Only user/assistant text, never reconstructed tool capabilities.
                self._engine.history.extend(('User' if r['role'] == 'user' else 'CLYDEX', r['content'])
                                            for r in records[-12:])
                return {'transcript': records, 'refresh': True}
            return self._intelligence_work(resume)

    def conversation_action(self, values):
        with self._lock:
            def change():
                previous = self._core.conversations.current.id
                result = self._core.data_actions.conversation(values)
                return dict(result=result, refresh=True, clear=previous != self._core.conversations.current.id)
            return self._intelligence_work(change)

    def export_conversation(self, key=None):
        with self._lock:
            if self._busy or self._core.voice.privacy.refresh():
                return ''
            return self._core.conversations.export(key)

    def memories(self):
        with self._lock:
            if self._core.voice.privacy.refresh():
                return {'locked': True}
            if self._busy:
                return {'busy': True}
            return dict(records=self._core.memory.repository.list(), proposals=list(self._core.memory.pending.values()),
                        policy=self._core.memory.policy())

    def memory_action(self, values):
        with self._lock:
            return self._intelligence_work(lambda: dict(result=self._core.data_actions.memory_action(values), refresh=True))

    def configure_memory(self, values):
        with self._lock:
            return self._intelligence_work(lambda: dict(result=self._core.data_actions.configure_memory(values), refresh=True))
