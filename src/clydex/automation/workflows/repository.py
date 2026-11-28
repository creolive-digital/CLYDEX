"""Owner-bound DPAPI records and compare-and-swap workflow versions.

Execution history retains statuses, not arguments, output or reusable approvals.
"""
import time
import uuid

from clydex.core.contracts import canonical_json
from clydex.security.schema import detached

CATEGORIES = ('workflow', 'trigger', 'feed', 'plugin', 'integration', 'mcp', 'profile')


class OperatingRepository:
    def __init__(self, store, owner, cipher):
        self.store, self.owner, self.cipher = store, owner, cipher
        with store._lock, store.connect() as connection:
            connection.execute("UPDATE workflow_runs SET status='interrupted',finished_at=? WHERE owner=? AND status='running'",
                               (time.time(), owner))

    def _role(self, category, key):
        if category not in CATEGORIES or type(key) is not str or str(uuid.UUID(key)) != key:
            raise ValueError('Invalid operating record identity.')
        return f'{self.owner}:operating:{category}:{key}'

    def get(self, category, key):
        role = self._role(category, key)
        with self.store._lock, self.store.connect() as connection:
            row = connection.execute('SELECT revision,payload FROM operating_records WHERE owner=? AND category=? AND id=?',
                                     (self.owner, category, key)).fetchone()
        if row is None:
            raise ValueError('Operating record not found.')
        return dict(id=key, revision=row[0], value=self.cipher.open(row[1], role))

    def list(self, category):
        if category not in CATEGORIES:
            raise ValueError('Unknown operating record category.')
        with self.store._lock, self.store.connect() as connection:
            rows = connection.execute('SELECT id,revision,payload FROM operating_records WHERE owner=? AND category=? ORDER BY id LIMIT 256',
                                      (self.owner, category)).fetchall()
        return [dict(id=key, revision=revision, value=self.cipher.open(payload, self._role(category, key)))
                for key, revision, payload in rows]

    def save(self, category, key, value, expected_revision):
        role = self._role(category, key)
        if type(expected_revision) is not int or expected_revision < 0 or len(canonical_json(value).encode('utf-8')) > 65536:
            raise ValueError('Invalid operating record revision or size.')
        revision = expected_revision + 1
        payload = self.cipher.seal(detached(value), role)
        with self.store._lock, self.store.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT revision FROM operating_records WHERE owner=? AND category=? AND id=?',
                                     (self.owner, category, key)).fetchone()
            if (row[0] if row else 0) != expected_revision:
                raise ValueError('Operating record changed; reload before saving.')
            if not row and connection.execute('SELECT COUNT(*) FROM operating_records WHERE owner=? AND category=?',
                                             (self.owner, category)).fetchone()[0] >= 256:
                raise ValueError('Operating record quota reached.')
            connection.execute('INSERT INTO operating_records VALUES(?,?,?,?,?) ON CONFLICT(owner,category,id) '
                               'DO UPDATE SET revision=excluded.revision,payload=excluded.payload',
                               (self.owner, category, key, revision, payload))
            if category == 'workflow':
                connection.execute('INSERT INTO workflow_versions VALUES(?,?,?,?)', (self.owner, key, revision, payload))
                connection.execute('DELETE FROM workflow_versions WHERE owner=? AND id=? AND revision<=?',
                                   (self.owner, key, revision - 50))
        return dict(id=key, revision=revision, value=detached(value))

    def delete(self, category, key, revision):
        self._role(category, key)
        with self.store._lock, self.store.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            changed = connection.execute('DELETE FROM operating_records WHERE owner=? AND category=? AND id=? AND revision=?',
                                         (self.owner, category, key, revision)).rowcount
            if not changed:
                raise ValueError('Operating record changed or missing.')
            if category == 'workflow':
                connection.execute('DELETE FROM workflow_versions WHERE owner=? AND id=?', (self.owner, key))

    def versions(self, key):
        role = self._role('workflow', key)
        with self.store._lock, self.store.connect() as connection:
            rows = connection.execute('SELECT revision,payload FROM workflow_versions WHERE owner=? AND id=? ORDER BY revision DESC LIMIT 50',
                                      (self.owner, key)).fetchall()
        result = []
        for revision, payload in rows:
            value = self.cipher.open(payload, role)
            definition = value['definition']
            result.append(dict(revision=revision, name=definition['name'], nodes=len(definition['nodes']),
                               enabled=value['enabled'], origin=value['origin'] if 'origin' in value else 'local'))
        return result

    def version(self, key, revision):
        role = self._role('workflow', key)
        if type(revision) is not int or revision < 1:
            raise ValueError('Invalid workflow version.')
        with self.store._lock, self.store.connect() as connection:
            row = connection.execute('SELECT payload FROM workflow_versions WHERE owner=? AND id=? AND revision=?',
                                     (self.owner, key, revision)).fetchone()
        if row is None:
            raise ValueError('Retained workflow version not found.')
        return self.cipher.open(row[0], role)

    def start_run(self, key, revision):
        self._role('workflow', key)
        run_id = str(uuid.uuid4())
        payload = self.cipher.seal({}, self.owner + ':run:' + run_id)
        with self.store._lock, self.store.connect() as connection:
            connection.execute('INSERT INTO workflow_runs VALUES(?,?,?,?,?,?,?,?)',
                               (self.owner, run_id, key, revision, 'running', time.time(), None, payload))
            connection.execute('DELETE FROM workflow_runs WHERE owner=? AND id NOT IN '
                               '(SELECT id FROM workflow_runs WHERE owner=? ORDER BY started_at DESC LIMIT 200)',
                               (self.owner, self.owner))
        return run_id

    def finish_run(self, run_id, status, nodes):
        if status not in ('running', 'complete', 'failed', 'cancelled', 'interrupted'):
            raise ValueError('Invalid execution status.')
        safe = {key: value for key, value in nodes.items() if value in ('running', 'complete', 'skipped')}
        payload = self.cipher.seal(safe, self.owner + ':run:' + run_id)
        with self.store._lock, self.store.connect() as connection:
            connection.execute('UPDATE workflow_runs SET status=?,finished_at=?,nodes=? WHERE owner=? AND id=?',
                               (status, None if status == 'running' else time.time(), payload, self.owner, run_id))

    def history(self):
        with self.store._lock, self.store.connect() as connection:
            rows = connection.execute('SELECT id,workflow_id,revision,status,started_at,finished_at,nodes '
                                      'FROM workflow_runs WHERE owner=? ORDER BY started_at DESC LIMIT 100', (self.owner,)).fetchall()
        return [dict(id=r[0], workflow_id=r[1], revision=r[2], status=r[3], started_at=r[4], finished_at=r[5],
                     nodes=self.cipher.open(r[6], self.owner + ':run:' + r[0])) for r in rows]

    def activity(self):
        """Existing content-free audit for this per-user runtime, not a new log."""
        with self.store._lock, self.store.connect() as connection:
            rows = connection.execute('SELECT event_id,created_at,action_id,tool,outcome FROM audit_events '
                                      'ORDER BY event_id DESC LIMIT 100').fetchall()
        return [dict(zip(('id', 'created_at', 'digest', 'tool', 'outcome'), row)) for row in rows]

    def claim_event(self, trigger_id, digest, now, ttl=86400):
        self._role('trigger', trigger_id)
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Invalid event digest.')
        with self.store._lock, self.store.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            connection.execute('DELETE FROM trigger_receipts WHERE owner=? AND expires_at<=?', (self.owner, now))
            if connection.execute('SELECT COUNT(*) FROM trigger_receipts WHERE owner=?', (self.owner,)).fetchone()[0] >= 4096:
                return False
            return bool(connection.execute('INSERT OR IGNORE INTO trigger_receipts VALUES(?,?,?,?)',
                                           (self.owner, trigger_id, digest, now + ttl)).rowcount)
