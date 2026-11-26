"""Encrypted owner-scoped memory records with revisions and content-free tombstones."""
from dataclasses import asdict
import re
import uuid

from clydex.conversations.models import identifier, utc_now
from clydex.core.errors import PermissionDenied
from clydex.memory.models import CATEGORIES, Memory
from clydex.security.content import validate_private_text


class MemoryRepository:
    def __init__(self, store, owner: str, cipher):
        self.store, self.owner, self.cipher = store, owner, cipher

    @staticmethod
    def validate(category, value, origin, source_kind, source_id, confirmed, local_only):
        if category not in CATEGORIES or origin not in ('explicit', 'inferred'):
            raise ValueError('Invalid memory classification.')
        validate_private_text(value, 2000)
        if source_kind not in ('user_prompt', 'manual_ui', 'conversation'):
            raise PermissionDenied('External/tool/mail content cannot become automatic memory.')
        if not isinstance(source_id, str) or (source_id and not re.fullmatch(r'[a-fA-F0-9-]{32,36}', source_id)):
            raise ValueError('Provenance must use a record identifier, never source content.')
        if type(confirmed) is not bool or type(local_only) is not bool:
            raise ValueError('Memory consent flags must be booleans.')

    def add(self, category, value, *, origin='explicit', source_kind='manual_ui', source_id='',
            confirmed=True, local_only=True) -> dict:
        self.validate(category, value, origin, source_kind, source_id, confirmed, local_only)
        now, key = utc_now(), str(uuid.uuid4())
        with self.store.connect() as db:
            count = db.execute('SELECT count(*) FROM memories WHERE owner=? AND status=?',
                               (self.owner, 'active')).fetchone()[0]
            if count >= 1000:
                raise PermissionDenied('Review existing memories before adding more.')
            db.execute('INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (key, self.owner, category, self.cipher.seal(value.strip(), self.owner), origin,
                        source_kind, source_id, int(confirmed), int(local_only), now, now, 'active', 1))
        return self.get(key)

    def get(self, key: str) -> dict:
        identifier(key)
        with self.store.connect() as db:
            row = db.execute('SELECT id,category,content,origin,source_kind,source_id,confirmed,local_only,'
                             'created_at,updated_at,revision,status FROM memories '
                             'WHERE id=? AND owner=? AND status=?', (key, self.owner, 'active')).fetchone()
        if row is None:
            raise PermissionDenied('Memory is absent or belongs to another owner.')
        return asdict(Memory(row[0], row[1], self.cipher.open(row[2], self.owner), row[3], row[4], row[5],
                             bool(row[6]), bool(row[7]), row[8], row[9], row[10], row[11]))

    def list(self) -> list[dict]:
        with self.store.connect() as db:
            ids = db.execute('SELECT id FROM memories WHERE owner=? AND status=? '
                             'ORDER BY updated_at DESC LIMIT 1000', (self.owner, 'active')).fetchall()
        return [self.get(key) for (key,) in ids]

    def update(self, key: str, value: str, *, local_only: bool, revision: int) -> dict:
        current = self.get(key)
        self.validate(current['category'], value, current['origin'], current['source_kind'],
                      current['source_id'], True, local_only)
        if type(revision) is not int or revision < 1:
            raise ValueError('Invalid memory revision.')
        with self.store.connect() as db:
            changed = db.execute('UPDATE memories SET content=?,local_only=?,confirmed=1,updated_at=?,'
                                 'revision=revision+1 WHERE id=? AND owner=? AND revision=? AND status=?',
                                 (self.cipher.seal(value.strip(), self.owner), int(local_only), utc_now(),
                                  key, self.owner, revision, 'active')).rowcount
            if changed != 1:
                raise PermissionDenied('Memory changed; review the latest revision.')
        return self.get(key)

    def delete(self, key: str, revision: int | None = None):
        current = self.get(key)
        revision = current['revision'] if revision is None else revision
        with self.store.connect() as db:
            changed = db.execute('UPDATE memories SET content=NULL,status=?,updated_at=?,revision=revision+1 '
                       'WHERE id=? AND owner=? AND revision=? AND status=?',
                       ('deleted', utc_now(), key, self.owner, revision, 'active')).rowcount
            if changed != 1:
                raise PermissionDenied('Memory changed after review.')
