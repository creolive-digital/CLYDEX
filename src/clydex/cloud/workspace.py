"""Core-owned cloud facade. All effects use the existing executor and serial queue."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import uuid
from urllib.parse import urlencode

from clydex.cloud.client import CloudClient, CloudConfig, CloudFailure
from clydex.core.contracts import canonical_json
from clydex.core.errors import PermissionDenied
from clydex.core.settings import read_settings, write_settings
from clydex.knowledge.cache import KnowledgeCache
from clydex.knowledge.ingestion import filename
from clydex.knowledge.retrieval import answer_question
from clydex.security.outbound import OutboundPolicy
from clydex.synchronization.contracts import identifier, validate_payload
from clydex.synchronization.local import LocalSync

FIELDS = {
    'login': {'login', 'password'}, 'refresh': set(), 'logout': set(), 'reload': set(),
    'collection.create': {'title', 'description'}, 'collection.delete': {'id', 'revision'},
    'document.delete': {'id', 'revision'}, 'document.reprocess': {'id', 'revision'},
    'document.versions': {'id'}, 'document.upload': {'selection', 'collection_id'},
    'document.version': {'selection', 'collection_id', 'id', 'revision'},
    'note.create': {'collection_id', 'title', 'text'},
    'search': {'query', 'mode', 'collection_id'}, 'ask': {'query', 'mode', 'collection_id'},
    'device.pair': {'display_name', 'platform', 'scopes'}, 'device.approve': {'id'},
    'device.revoke': {'id'}, 'device.rotate': {'id'},
    'sync.configure': {'policy'}, 'sync.enqueue': {'category', 'id', 'source_id', 'payload', 'deleted'},
    'sync.push': set(), 'sync.pull': set(), 'sync.apply': {'sequence'}, 'sync.theme': {'sequence'}, 'sync.discard': {'id'},
    'cache.add': {'id', 'hours', 'quota_bytes'}, 'cache.remove': {'id'}, 'cache.clear': set(),
    'offline.search': {'query'}, 'offline.ask': {'query'},
}


class CloudWorkspace:
    def __init__(self, core, owner, cipher):
        self.core, self.owner = core, owner
        self.path = core.paths.directory('settings') / 'cloud.json'
        self.error = ''
        try:
            configuration = CloudConfig(**read_settings(self.path))
        except (ValueError, TypeError, OSError):
            configuration, self.error = CloudConfig(), 'invalid_cloud_configuration'
        self.client = CloudClient(configuration)
        self.sync = LocalSync(core.store, owner, cipher, core.memory, core.conversations)
        self.cache = KnowledgeCache(self.sync)
        self.binding = ''
        self._account_path = core.paths.directory('settings') / 'cloud-account.json'
        try:
            last = read_settings(self._account_path)
            if last.get('endpoint') == configuration.endpoint and last.get('account_id'):
                self.binding = self.sync.binding(configuration.endpoint, last['account_id'])
        except (ValueError, TypeError, OSError):
            pass
        self._lock = threading.RLock()
        self.results, self.selections, self.revision = {}, {}, 0
        self.apply_theme = None  # Trusted desktop binds the existing preference service.

    def _guard(self):
        self.core.engine.cancel_token.check()
        if self.core.voice.privacy.refresh():
            raise PermissionDenied('Desktop locked.')
        routing = self.core.providers.routing
        OutboundPolicy.cloud_service(enabled=self.client.config.enabled,
            privacy=self.core.config.privacy_mode or self.core.personality.privacy_mode or routing.privacy,
            offline=routing.offline or routing.profile == 'offline', allow_cloud=self.core.config.allow_cloud)

    def lock(self):
        with self._lock:
            self.client.forget()
            self.results.clear()
            self.selections.clear()
            self.revision += 1

    def configure(self, values):
        configuration = CloudConfig(**values)
        def apply(arguments):
            self.lock()
            write_settings(self.path, arguments['configuration'])
            self.client.config = configuration
            self.client.forget()
            self.binding = ''
            return {'configured': True}
        return self.core.engine.execute_tool('cloud.configure', 'personal cloud connection',
            {'configuration': asdict(configuration)}, apply,
            'Save this HTTPS origin? Cloud remains subject to local privacy policy and separate exact-action transfer approval. '
            'Server-managed encryption allows the VPS to decrypt content; credentials remain in RAM. No data is synchronized now.')

    def _request(self, method, path, payload=None, **kwargs):
        self._guard()
        try:
            return self.client.request(method, path, payload, self.core.engine.cancel_token, **kwargs)
        except CloudFailure as exc:
            if exc.status in (401, 403) and self.binding:
                self.cache.purge(self.binding)
            raise
        except BaseException:
            if self.core.engine.cancel_token.is_set() or self.core.voice.privacy.locked:
                self.lock()
            raise

    def selection(self, paths, *, folder=False):
        """Called only with native picker output. No frontend path is accepted."""
        chosen = []
        if folder:
            base = Path(paths[0])
            if base.is_symlink() or not base.is_dir():
                raise ValueError('Unsafe folder selection.')
            # Explicit folder import is a bounded snapshot, never a watcher.
            inspected, deadline = 0, time.monotonic() + 3
            def visit(directory, depth):
                nonlocal inspected
                if depth > 3:
                    return
                with os.scandir(directory) as entries:
                    for entry in entries:
                        inspected += 1
                        if inspected > 500 or time.monotonic() > deadline:
                            raise ValueError('Selected folder exceeds inspection limits.')
                        path = Path(entry.path)
                        if (path.is_symlink() or path.name.startswith('.')
                                or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400
                                or base.resolve() not in path.resolve().parents):
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            visit(path, depth + 1)
                        elif entry.is_file(follow_symlinks=False):
                            chosen.append(path)
                            if len(chosen) > 16:
                                raise ValueError('Select at most 16 files per folder import.')
            visit(base, 0)
        else:
            chosen = [Path(x) for x in paths]
        if not 1 <= len(chosen) <= 16:
            raise ValueError('Select 1–16 files.')
        values, total = {}, 0
        for path in chosen:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
                raise ValueError('Unsafe or oversized file.')
            filename(path.name)
            total += path.stat().st_size
            if total > 20 * 1024 * 1024:
                raise ValueError('Selected files exceed 20 MiB.')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            key = str(uuid.uuid4())
            values[key] = dict(path=path, name=path.name, size_bytes=path.stat().st_size, sha256=digest,
                               operation_id=str(uuid.uuid4()), expires=time.monotonic() + 600)
        with self._lock:
            self.selections = values
            self.revision += 1
        return {'selected': len(values)}

    def _local_review(self, operation, data, action):
        return self.core.engine.execute_tool('knowledge.cache' if operation.startswith(('cache.', 'offline.')) else 'sync.apply',
            'local encrypted knowledge/synchronization', {'operation': operation, 'data': data} if operation.startswith(('cache.', 'offline.'))
            else {'change': dict(operation=operation, data=data)}, lambda _: action(),
            'Apply this local data change? Incoming content is untrusted; permissions and microphone consent are unchanged.')

    def execute(self, operation, values):
        if operation not in FIELDS or not isinstance(values, dict) or set(values) != FIELDS[operation]:
            raise ValueError('Unknown cloud operation or fields.')
        values = json.loads(canonical_json(values))
        if len(canonical_json(values).encode()) > 60000:
            raise ValueError('Cloud bridge request exceeds its bound.')
        engine = self.core.engine
        try:
            result = self._execute(operation, values)
            engine.cancel_token.check()
            with self._lock:
                self.results[operation] = result
                self.error = ''
                self.revision += 1
            return {'cloud_refresh': True}
        except CloudFailure as exc:
            with self._lock:
                self.error = exc.code
                self.revision += 1
            if exc.status in (401, 403) and self.binding:
                self.cache.purge(self.binding)
            raise

        except BaseException:
            if engine.cancel_token.is_set() or self.core.voice.privacy.locked:
                self.lock()
            raise

    def _execute(self, op, values):
        engine, cancel = self.core.engine, self.core.engine.cancel_token
        if op.startswith(('offline.', 'cache.remove', 'cache.clear', 'sync.enqueue', 'sync.apply', 'sync.theme', 'sync.discard')):
            if not self.binding:
                raise PermissionDenied('Select a previously authenticated cloud account first.')
            if op.startswith('offline.'):
                result = self.cache.search(self.binding, values['query'])
                return answer_question(engine, values['query'], result, offline=True) if op == 'offline.ask' else result
            if op == 'cache.remove':
                identifier(values['id'])
                return self._local_review(op, values, lambda: self.cache.purge(self.binding, values['id']) or {'deleted': True})
            if op == 'cache.clear':
                return self._local_review(op, values, lambda: self.cache.purge(self.binding) or {'deleted': True})
            if op == 'sync.discard':
                return self._local_review(op, values, lambda: self.sync.discard(self.binding, values['id']) or {'discarded': True})
            if op in ('sync.apply', 'sync.theme'):
                change = next((c for c in self.sync.inbox(self.binding) if c['sequence'] == values['sequence']), None)
                if not change:
                    raise ValueError('Inbound change absent.')
                if op == 'sync.theme':
                    if change['category'] != 'themes' or change['deleted'] or self.apply_theme is None:
                        raise PermissionDenied('No applicable incoming appearance settings.')
                    payload = validate_payload('themes', change['payload'])
                    return engine.execute_tool('desktop.configure', 'incoming appearance preferences', {'values': payload},
                        lambda a: self.apply_theme(a['values']), 'Apply this incoming appearance using the existing local presentation policy? '
                        'Startup, microphone, permissions and credentials cannot be imported as themes.')
                return self._local_review(op, change, lambda: self.sync.apply(self.binding, change,
                    current_conversation=self.core.conversations.current.id))
            identifier(values['id'])
            if values['category'] in ('memory', 'history'):
                # IDs alone are accepted for these categories; arbitrary frontend text cannot impersonate source records.
                if values['source_id'] != values['id'] or values['payload'] or values['deleted']:
                    raise ValueError('Saved memory/history must be exported by existing source ID.')
                payload, _ = self.sync._source(values['category'], values['source_id'])
                validate_payload(values['category'], payload)
            else:
                payload = validate_payload(values['category'], values['payload'], deleted=values['deleted'])
            return self._local_review(op, dict(values, payload=payload), lambda: self.sync.enqueue(self.binding,
                values['category'], values['id'], payload, source_id=values['source_id'], deleted=values['deleted']))
        self._guard()
        if op.startswith(('sync.', 'cache.')) and not self.binding:
            raise PermissionDenied('Authenticate this account before configuring synchronization.')
        # Exact immutable review contains all transmitted data except reusable credentials.
        review, secret_digest = dict(values), ''
        if op == 'login':
            if (not isinstance(values['login'], str) or not 3 <= len(values['login']) <= 160
                    or not isinstance(values['password'], str) or not 1 <= len(values['password']) <= 256):
                raise ValueError('Invalid login.')
            secret_digest = hashlib.sha256(values['password'].encode()).hexdigest()
            review.pop('password')
        if op == 'sync.push':
            review = {'operations': self.sync.queued(self.binding)}
            if not review['operations']:
                return {'sent': 0}
        if op in ('document.upload', 'document.version'):
            selection = self.selections.get(values['selection'])
            if not selection or selection['expires'] < time.monotonic():
                raise ValueError('File selection expired; select it again.')
            review = dict(values, file={k: selection[k] for k in ('name', 'size_bytes', 'sha256', 'operation_id')})
        arguments = dict(operation=op, destination=self.client.config.endpoint, data=review, credential_digest=secret_digest)
        def perform(approved):
            self._guard()
            if approved['destination'] != self.client.config.endpoint:
                raise PermissionDenied('Cloud destination changed.')
            if op == 'login':
                self.results.clear()
                result = self.client.login(values['login'], values['password'], cancel)
                self.binding = self.sync.binding(self.client.config.endpoint, self.client.account_id)
                write_settings(self._account_path, {'endpoint': self.client.config.endpoint, 'account_id': self.client.account_id})
                return result
            if op == 'refresh':
                return self.client.rotate(cancel)
            if op == 'logout':
                try:
                    return self._request('POST', '/v1/auth/logout')
                finally:
                    self.client.forget()
                    self.results.clear()
            if op == 'reload':
                endpoints = {'collections': '/v1/collections', 'documents': '/v1/documents', 'devices': '/v1/devices',
                    'jobs': '/v1/jobs', 'usage': '/v1/storage/usage', 'capabilities': '/v1/status', 'sync_policy': '/v1/sync/preferences'}
                return {key: self._request('GET', path) for key, path in endpoints.items()}
            if op in ('search', 'ask'):
                payload = dict(values, limit=5)
                if not payload['collection_id']:
                    payload.pop('collection_id')
                result = self._request('POST', '/v1/knowledge/search', payload)
                return answer_question(engine, values['query'], result) if op == 'ask' else result
            if op == 'collection.create':
                return self._request('POST', '/v1/collections', values)
            if op == 'note.create':
                return self._request('POST', '/v1/notes', dict(values, operation_id=str(uuid.uuid4())))
            if op in ('collection.delete', 'document.delete', 'document.reprocess', 'document.versions'):
                key = identifier(values['id'])
                kind = 'collections' if op.startswith('collection.') else 'documents'
                path = f'/v1/{kind}/{key}'
                method = 'DELETE'
                if op == 'document.reprocess':
                    path += '/processing'
                    method = 'POST'
                if op == 'document.versions':
                    return self._request('GET', path + '/versions')
                if type(values['revision']) is not int or values['revision'] < 1:
                    raise ValueError('Invalid expected revision.')
                result = self._request(method, path + '?' + urlencode({'expected_revision': values['revision']}))
                if op == 'document.delete':
                    self.cache.purge(self.binding, key)
                return result
            if op.startswith('document.'):
                collection = identifier(values['collection_id'])
                item = self.selections[values['selection']]
                path = item['path']
                if item['expires'] < time.monotonic() or path.is_symlink() or path.stat().st_size != item['size_bytes']:
                    raise PermissionDenied('Selected file changed or expired.')
                content = path.read_bytes()
                if hashlib.sha256(content).hexdigest() != item['sha256']:
                    raise PermissionDenied('Selected file changed after review.')
                query = {'name': item['name']}
                route = f'/v1/collections/{collection}/documents'
                if op == 'document.version':
                    route = '/v1/documents/' + identifier(values['id']) + '/versions'
                    query.update(collection_id=collection, expected_revision=values['revision'])
                return self._request('POST', route + '?' + urlencode(query), raw=content, operation_id=item['operation_id'])
            if op == 'device.pair':
                return self._request('POST', '/v1/devices/pairings', values)
            if op.startswith('device.'):
                key = identifier(values['id'])
                if op == 'device.approve':
                    return self._request('POST', f'/v1/devices/pairings/{key}/approval')
                if op == 'device.revoke':
                    return self._request('DELETE', '/v1/devices/' + key)
                # Never return reusable rotated credentials to the WebView.
                self._request('POST', f'/v1/devices/{key}/credentials')
                return {'rotated': True, 're_pair_required': True}
            if op == 'sync.configure':
                # Local disable takes effect even if remote update fails; nothing runs automatically.
                self.sync.configure(self.binding, values['policy'])
                return self._request('PUT', '/v1/sync/preferences', values['policy'])
            if op == 'sync.push':
                if self.sync.queued(self.binding) != approved['data']['operations']:
                    raise PermissionDenied('Queued source changed after approval.')
                operations = approved['data']['operations']
                try:
                    result = self._request('POST', '/v1/sync/operations', {'operations': operations})
                    if len(result['results']) != len(operations):
                        raise CloudFailure('invalid_acknowledgement')
                    for operation, acknowledged in zip(operations, result['results']):
                        self.sync.acknowledged(self.binding, operation, acknowledged)
                    return {'sent': len(operations)}
                except Exception as exc:
                    for operation in operations:
                        self.sync.failed(self.binding, operation['operation_id'], 'revision_conflict' if getattr(exc, 'status', 0) == 409 else 'transfer_interrupted',
                            conflict=getattr(exc, 'status', 0) == 409)
                    raise
            if op == 'sync.pull':
                result = self._request('GET', '/v1/sync/changes?' + urlencode({'cursor': self.sync.cursor(self.binding), 'limit': 20}))
                self.sync.stage(self.binding, result)
                return {'staged': len(result['changes']), 'has_more': result['has_more']}
            if op == 'cache.add':
                key = identifier(values['id'])
                items, offset = [], 0
                while True:
                    result = self._request('GET', f'/v1/documents/{key}/excerpts?' + urlencode({'offset': offset, 'limit': 20}))
                    items.extend(result['items'])
                    if len(items) > 2000:
                        raise ValueError('Excerpt limit reached.')
                    if not result['truncated']:
                        break
                    if not result['items']:
                        raise CloudFailure('invalid_excerpt_page')
                    offset = result['items'][-1]['ordinal'] + 1
                return self.core.engine.execute_tool('knowledge.cache', 'selected offline document excerpts',
                    {'operation': 'cache.add', 'data': dict(values, excerpt_count=len(items))},
                    lambda _: self.cache.put(self.binding, key, items, hours=values['hours'], quota_bytes=values['quota_bytes']),
                    'Store these excerpts using Windows DPAPI? Offline access expires at the selected time; remote revocation cannot reach a disconnected device.')
            raise ValueError('Unknown operation.')
        return engine.execute_tool('cloud.request', self.client.config.endpoint, arguments, perform,
            'Transfer the displayed data to/from this personal cloud service? Server administrators can decrypt stored content. '
            'Approving this action does not enable automatic synchronization. Stop prevents subsequent actions; completed remote effects remain.')

    def snapshot(self):
        with self._lock:
            result = dict(configuration=asdict(self.client.config), status=self.client.status, account_id=self.client.account_id,
                error=self.error, revision=self.revision, results=json.loads(canonical_json(self.results)),
                selections=[dict(id=key, **{k: v[k] for k in ('name', 'size_bytes', 'sha256')}) for key, v in self.selections.items()
                            if v['expires'] > time.monotonic()])
            if self.binding:
                result.update(synchronization=self.sync.snapshot(self.binding), cache=self.cache.snapshot(self.binding))
            return result

    def close(self):
        self.lock()

    def wait_closed(self):
        pass  # Network work belongs to Core's supervised queue, which Core joins.
