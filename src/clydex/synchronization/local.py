"""DPAPI outbox and reviewed inbox; mapping and source imports commit atomically.

No network work is automatic. Account/origin binding prevents cross-account
replay. Local-only/private history never enters the outbox. Conflict resolution
requires a new explicit decision; stale queued operations are not rewritten.
"""
import hashlib
import json
import time
import uuid
from clydex.core.contracts import canonical_json
from clydex.core.errors import PermissionDenied
from clydex.synchronization.contracts import CATEGORIES, identifier, validate_payload


class LocalSync:
    def __init__(self, store, owner, cipher, memory, conversations, clock=time.time):
        self.store, self.owner, self.cipher = store, owner, cipher
        self.memory, self.conversations, self.clock = memory, conversations, clock

    @staticmethod
    def binding(endpoint, account):
        identifier(account)
        return hashlib.sha256((endpoint.rstrip('/') + '/' + account).encode()).hexdigest()

    def seal(self, binding, role, value):
        return self.cipher.seal(value, self.owner + ':' + binding + ':' + role)

    def open(self, binding, role, value):
        return self.cipher.open(value, self.owner + ':' + binding + ':' + role)

    def policy(self, binding):
        with self.store.connect() as c:
            row = c.execute('SELECT policy FROM sync_state WHERE owner=? AND binding=?', (self.owner, binding)).fetchone()
        return self.open(binding, 'policy', row[0]) if row else {x: False for x in CATEGORIES}

    def configure(self, binding, policy):
        if set(policy) != set(CATEGORIES) or any(type(v) is not bool for v in policy.values()):
            raise ValueError('Every sync category needs explicit boolean consent.')
        previous = self.policy(binding)
        replay = any(policy[x] and not previous[x] for x in CATEGORIES)
        with self.store.connect() as c:
            c.execute('INSERT INTO sync_state VALUES(?,?,0,?) ON CONFLICT(owner,binding) DO UPDATE SET policy=excluded.policy,'
                      'cursor=CASE WHEN ? THEN 0 ELSE sync_state.cursor END',
                      (self.owner, binding, self.seal(binding, 'policy', policy), replay))
        return policy

    def _source(self, category, source_id):
        if category == 'memory':
            value = self.memory.repository.get(source_id)
            return {k: value[k] for k in ('category', 'value', 'local_only', 'confirmed', 'origin', 'source_kind')}, value['revision']
        if category == 'history':
            repository = self.conversations.repository
            conversation = repository.get(source_id)
            messages = repository.export_messages(source_id)
            with self.store.connect() as c:
                revision = c.execute('SELECT revision FROM conversations WHERE id=? AND owner=?', (source_id, self.owner)).fetchone()[0]
            return dict(title=conversation.title, messages=[{k: m[k] for k in ('role', 'content', 'provider', 'model', 'created_at')} for m in messages],
                        temporary=False, local_only=False, sensitive=False), revision
        raise ValueError('Only existing saved memory/history uses source export.')

    def enqueue(self, binding, category, entity_id, payload=None, *, source_id='', deleted=False):
        identifier(entity_id)
        if not self.policy(binding).get(category):
            raise PermissionDenied('Synchronization category is disabled.')
        revision = 0
        if source_id and not deleted:
            current, revision = self._source(category, source_id)
            if payload is not None and canonical_json(current) != canonical_json(payload):
                raise PermissionDenied('Source changed after review.')
            payload = current
        payload = validate_payload(category, payload or {}, deleted=deleted)
        key = str(uuid.uuid4())
        with self.store.connect() as c:
            if c.execute('SELECT count(*) FROM sync_outbox WHERE owner=? AND binding=?', (self.owner, binding)).fetchone()[0] >= 500:
                raise PermissionDenied('Review and remove queued synchronization changes first.')
            row = c.execute('SELECT version FROM sync_links WHERE owner=? AND binding=? AND category=? AND entity_id=?',
                            (self.owner, binding, category, entity_id)).fetchone()
            if c.execute('SELECT 1 FROM sync_outbox WHERE owner=? AND binding=? AND category=? AND entity_id=?',
                         (self.owner, binding, category, entity_id)).fetchone():
                raise PermissionDenied('An operation for this entity is already queued.')
            operation = dict(operation_id=key, category=category, entity_id=entity_id, base_version=row[0] if row else 0,
                             payload=payload, deleted=deleted)
            c.execute('INSERT INTO sync_outbox(id,owner,binding,category,entity_id,base_version,payload,source_id,source_revision,status) '
                      'VALUES(?,?,?,?,?,?,?,?,?,?)', (key, self.owner, binding, category, entity_id, operation['base_version'],
                      self.seal(binding, 'outbox:' + key, operation), source_id, revision, 'queued'))
        return operation

    def queued(self, binding):
        with self.store.connect() as c:
            rows = c.execute('SELECT id,payload,category,source_id,source_revision,attempts FROM sync_outbox '
                'WHERE owner=? AND binding=? AND status=? AND next_attempt<=? ORDER BY rowid LIMIT 20',
                (self.owner, binding, 'queued', self.clock())).fetchall()
        values = []
        for key, payload, category, source, revision, attempts in rows:
            if not self.policy(binding).get(category):
                continue
            value = self.open(binding, 'outbox:' + key, payload)
            if source and not value['deleted']:
                try:
                    current, actual_revision = self._source(category, source)
                    validate_payload(category, current)
                    if actual_revision != revision or canonical_json(current) != canonical_json(value['payload']):
                        raise ValueError('Source changed.')
                except (PermissionDenied, ValueError):
                    self.failed(binding, key, 'source_changed', conflict=True)
                    continue
            values.append(value)
        return values

    def failed(self, binding, key, code, *, conflict=False):
        with self.store.connect() as c:
            row = c.execute('SELECT attempts FROM sync_outbox WHERE owner=? AND binding=? AND id=?', (self.owner, binding, key)).fetchone()
            if row:
                attempt = row[0] + 1
                c.execute('UPDATE sync_outbox SET attempts=?,status=?,next_attempt=?,error=? WHERE owner=? AND binding=? AND id=?',
                    (attempt, 'conflict' if conflict else 'failed' if attempt >= 5 else 'queued',
                     self.clock() + min(300, 2**attempt), code, self.owner, binding, key))

    def acknowledged(self, binding, operation, result):
        if result['entity_id'] != operation['entity_id'] or result['version'] != operation['base_version'] + 1:
            raise ValueError('Invalid cloud operation acknowledgement.')
        with self.store.connect() as c:
            row = c.execute('SELECT source_id,source_revision FROM sync_outbox WHERE owner=? AND binding=? AND id=?',
                            (self.owner, binding, operation['operation_id'])).fetchone()
            if not row:
                return
            c.execute('INSERT INTO sync_links VALUES(?,?,?,?,?,?,?) ON CONFLICT(owner,binding,category,entity_id) DO UPDATE '
                      'SET local_id=excluded.local_id,local_revision=excluded.local_revision,version=excluded.version',
                      (self.owner, binding, operation['category'], operation['entity_id'], row[0], row[1], result['version']))
            c.execute('DELETE FROM sync_outbox WHERE owner=? AND binding=? AND id=?', (self.owner, binding, operation['operation_id']))

    def cursor(self, binding):
        with self.store.connect() as c:
            row = c.execute('SELECT cursor FROM sync_state WHERE owner=? AND binding=?', (self.owner, binding)).fetchone()
        return row[0] if row else 0

    def stage(self, binding, page):
        if (not isinstance(page.get('changes'), list) or len(page['changes']) > 100
                or type(page.get('cursor')) is not int or page['cursor'] < self.cursor(binding)):
            raise ValueError('Invalid synchronization page.')
        policy = self.policy(binding)
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            for item in page['changes']:
                category, entity = item['category'], identifier(item['entity_id'])
                if category not in CATEGORIES or not policy[category]:
                    continue
                sequence, version, deleted = item['sequence'], item['version'], item['deleted']
                if (type(sequence) is not int or not 0 < sequence <= page['cursor'] or type(version) is not int
                        or version < 1 or type(deleted) is not bool):
                    raise ValueError('Invalid change metadata.')
                if len(canonical_json(item).encode()) > 65536:
                    raise ValueError('Change exceeds bound.')
                if deleted:
                    c.execute('DELETE FROM sync_inbox WHERE owner=? AND binding=? AND category=? AND entity_id=? AND version<?',
                              (self.owner, binding, category, entity, version))
                if category == 'knowledge':
                    c.execute('DELETE FROM knowledge_cache WHERE owner=? AND binding=? AND document_id=? '
                              'AND (revision<? OR ?)', (self.owner, binding, entity, item['payload'].get('revision', -1), deleted))
                count = c.execute('SELECT count(*) FROM sync_inbox WHERE owner=? AND binding=?', (self.owner, binding)).fetchone()[0]
                if count >= 500:
                    raise PermissionDenied('Apply or dismiss pending inbound changes before fetching more.')
                c.execute('INSERT OR IGNORE INTO sync_inbox VALUES(?,?,?,?,?,?,?,?)', (self.owner, binding, sequence,
                    category, entity, version, int(deleted), self.seal(binding, 'inbox:' + str(sequence), item['payload'])))
            c.execute('UPDATE sync_state SET cursor=? WHERE owner=? AND binding=?', (page['cursor'], self.owner, binding))

    def inbox(self, binding):
        with self.store.connect() as c:
            rows = c.execute('SELECT sequence,category,entity_id,version,deleted,payload FROM sync_inbox WHERE owner=? AND binding=? '
                             'ORDER BY sequence LIMIT 100', (self.owner, binding)).fetchall()
        return [dict(sequence=r[0], category=r[1], entity_id=r[2], version=r[3], deleted=bool(r[4]),
                     payload=self.open(binding, 'inbox:' + str(r[0]), r[5])) for r in rows]

    def apply(self, binding, change, *, current_conversation=''):
        category, entity = change['category'], change['entity_id']
        if not self.policy(binding).get(category):
            raise PermissionDenied('Category disabled.')
        value = change['payload']
        if category != 'knowledge':
            value = validate_payload(category, value, deleted=change['deleted'])
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            pending = c.execute('SELECT payload FROM sync_inbox WHERE owner=? AND binding=? AND sequence=?',
                                (self.owner, binding, change['sequence'])).fetchone()
            if not pending or self.open(binding, 'inbox:' + str(change['sequence']), pending[0]) != change['payload']:
                raise PermissionDenied('Inbound change changed or is absent.')
            link = c.execute('SELECT local_id,local_revision,version FROM sync_links WHERE owner=? AND binding=? AND category=? AND entity_id=?',
                             (self.owner, binding, category, entity)).fetchone()
            if link and change['version'] <= link[2]:
                c.execute('DELETE FROM sync_inbox WHERE owner=? AND binding=? AND sequence=?', (self.owner, binding, change['sequence']))
                return {'duplicate': True}
            if c.execute('SELECT 1 FROM sync_outbox WHERE owner=? AND binding=? AND category=? AND entity_id=?',
                         (self.owner, binding, category, entity)).fetchone():
                raise PermissionDenied('Local queued change conflicts with this remote revision.')
            local_id, revision = (link[0], link[1]) if link else (str(uuid.uuid4()), 0)
            if category in ('memory', 'history'):
                table = 'memories' if category == 'memory' else 'conversations'
                row = c.execute(f'SELECT revision,status FROM {table} WHERE id=? AND owner=?', (local_id, self.owner)).fetchone()
                if row and (row[0] != revision or row[1] == 'deleted' or local_id == current_conversation):
                    raise PermissionDenied('Local revision or active conversation conflicts; preserve it and review separately.')
                if category == 'memory':
                    privacy = c.execute('SELECT local_only FROM memories WHERE id=? AND owner=?', (local_id, self.owner)).fetchone()
                    if privacy and privacy[0]:
                        raise PermissionDenied('Local-only memory cannot be overwritten or deleted remotely.')
                    if not self.memory.policy()['enabled']:
                        raise PermissionDenied('Memory disabled.')
                    self.memory.repository.apply_sync(c, local_id, value, change['deleted'])
                else:
                    self.conversations.repository.apply_sync(c, local_id, value, change['deleted'])
                row = c.execute(f'SELECT revision FROM {table} WHERE id=? AND owner=?', (local_id, self.owner)).fetchone()
                revision = row[0] if row else 0
            elif category == 'preferences' and not change['deleted']:
                # Preference imports do not activate a microphone or alter security.
                for key, item in value.items():
                    self.store._validate_setting(key, item, True)
                    c.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, json.dumps(item)))
            c.execute('INSERT INTO sync_replicas VALUES(?,?,?,?,?,?,?) ON CONFLICT(owner,binding,category,entity_id) DO UPDATE '
                      'SET payload=excluded.payload,version=excluded.version,deleted=excluded.deleted',
                      (self.owner, binding, category, entity, None if change['deleted'] else self.seal(binding, 'replica:' + entity, value),
                       change['version'], change['deleted']))
            c.execute('INSERT INTO sync_links VALUES(?,?,?,?,?,?,?) ON CONFLICT(owner,binding,category,entity_id) DO UPDATE SET '
                      'local_id=excluded.local_id,local_revision=excluded.local_revision,version=excluded.version',
                      (self.owner, binding, category, entity, local_id, revision, change['version']))
            c.execute('DELETE FROM sync_inbox WHERE owner=? AND binding=? AND sequence=?', (self.owner, binding, change['sequence']))
        return {'applied': True, 'category': category, 'local_id': local_id}

    def discard(self, binding, key):
        identifier(key)
        with self.store.connect() as c:
            c.execute('DELETE FROM sync_outbox WHERE owner=? AND binding=? AND id=?', (self.owner, binding, key))

    def replicas(self, binding, category):
        if category not in CATEGORIES:
            raise ValueError('Unknown replica category.')
        with self.store.connect() as c:
            rows = c.execute('SELECT entity_id,version,payload FROM sync_replicas WHERE owner=? AND binding=? '
                             'AND category=? AND deleted=0 ORDER BY entity_id LIMIT 100',
                             (self.owner, binding, category)).fetchall()
        return [dict(id=key, version=version, payload=self.open(binding, 'replica:' + key, payload))
                for key, version, payload in rows]

    def snapshot(self, binding):
        with self.store.connect() as c:
            queued = c.execute('SELECT id,category,entity_id,status,attempts,error,next_attempt FROM sync_outbox WHERE owner=? AND binding=? '
                               'ORDER BY rowid LIMIT 100', (self.owner, binding)).fetchall()
        return dict(policy=self.policy(binding), cursor=self.cursor(binding), inbox=self.inbox(binding),
                    outbox=[dict(zip(('id', 'category', 'entity_id', 'status', 'attempts', 'error', 'next_attempt'), r)) for r in queued])
