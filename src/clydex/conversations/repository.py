"""Parameterized owner-scoped SQL. Private titles/messages are DPAPI ciphertext."""
from __future__ import annotations
from dataclasses import asdict
import uuid

from clydex.conversations.models import Conversation, identifier, utc_now
from clydex.core.errors import PermissionDenied
from clydex.security.content import validate_private_text


class ConversationRepository:
    def __init__(self, store, owner: str, cipher):
        self.store, self.owner, self.cipher = store, owner, cipher

    def create(self, title: str) -> Conversation:
        title = validate_private_text(title, 120)
        now, key = utc_now(), str(uuid.uuid4())
        payload = self.cipher.seal(title, self.owner)
        with self.store.connect() as db:
            db.execute('INSERT INTO conversations(id,owner,title,created_at,updated_at,status) '
                       'VALUES(?,?,?,?,?,?)', (key, self.owner, payload, now, now, 'active'))
        return Conversation(key, title, False, now, now)

    def get(self, key: str) -> Conversation:
        identifier(key)
        with self.store.connect() as db:
            row = db.execute('SELECT id,title,created_at,updated_at,status FROM conversations '
                             'WHERE id=? AND owner=? AND status<>?', (key, self.owner, 'deleted')).fetchone()
        if row is None:
            raise PermissionDenied('Conversation is absent or belongs to another owner.')
        return Conversation(row[0], self.cipher.open(row[1], self.owner), False, row[2], row[3], row[4])

    def list(self, query: str = '', include_archived: bool = True) -> list[dict]:
        if not isinstance(query, str) or len(query) > 200:
            raise ValueError('Invalid search query.')
        with self.store.connect() as db:
            rows = db.execute('SELECT id FROM conversations WHERE owner=? AND status<>? '
                              'ORDER BY updated_at DESC LIMIT 500', (self.owner, 'deleted')).fetchall()
        result = []
        matching = set()
        if query:
            with self.store.connect() as db:
                recent = db.execute('SELECT conversation_id,content FROM messages WHERE owner=? '
                                    'ORDER BY rowid DESC LIMIT 10000', (self.owner,))
                for key, content in recent:
                    if query.casefold() in self.cipher.open(content, self.owner).casefold():
                        matching.add(key)
        for row in rows:
            conversation = self.get(row[0])
            if not include_archived and conversation.status == 'archived':
                continue
            if query.casefold() in conversation.title.casefold():
                result.append(asdict(conversation))
            elif conversation.id in matching:
                result.append(asdict(conversation))
        return result

    def messages(self, key: str, limit: int = 100) -> list[dict]:
        self.get(key)
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError('Invalid history page size.')
        with self.store.connect() as db:
            rows = db.execute('SELECT id,role,content,created_at,provider,model FROM messages '
                              'WHERE conversation_id=? AND owner=? ORDER BY created_at DESC,rowid DESC LIMIT ?',
                              (key, self.owner, limit)).fetchall()
        return [dict(id=r[0], role=r[1], content=self.cipher.open(r[2], self.owner), created_at=r[3],
                     provider=r[4], model=r[5]) for r in reversed(rows)]

    def export_messages(self, key: str) -> list[dict]:
        self.get(key)
        result, size = [], 0
        with self.store.connect() as db:
            rows = db.execute('SELECT id,role,content,created_at,provider,model FROM messages '
                              'WHERE conversation_id=? AND owner=? ORDER BY rowid', (key, self.owner))
            for row in rows:
                content = self.cipher.open(row[2], self.owner)
                size += len(content.encode('utf-8')) + 1024
                if size > 8 * 1024 * 1024:
                    raise ValueError('Conversation exceeds the 8 MiB export limit; no partial export produced.')
                result.append(dict(id=row[0], role=row[1], content=content, created_at=row[3], provider=row[4], model=row[5]))
        return result

    def append_pair(self, key: str, prompt: str, answer: str, provider: str, model: str):
        self.get(key)
        prompt, answer = validate_private_text(prompt), validate_private_text(answer)
        if provider not in ('', 'local', 'codex', 'openai', 'anthropic', 'gemini', 'ollama', 'openrouter', 'custom'):
            raise ValueError('Invalid provider metadata.')
        if not isinstance(model, str) or len(model) > 200:
            raise ValueError('Invalid model metadata.')
        if model:
            validate_private_text(model, 200)
        now = utc_now()
        payloads = [(str(uuid.uuid4()), key, self.owner, role, self.cipher.seal(text, self.owner), now, provider, model)
                    for role, text in (('user', prompt), ('assistant', answer))]
        with self.store.connect() as db:
            changed = db.execute('UPDATE conversations SET updated_at=?,revision=revision+1 '
                                 'WHERE id=? AND owner=? AND status=?', (now, key, self.owner, 'active')).rowcount
            if changed != 1:
                raise PermissionDenied('Archived or deleted conversations cannot receive messages.')
            db.executemany('INSERT INTO messages VALUES(?,?,?,?,?,?,?,?)', payloads)

    def update(self, key: str, *, title: str | None = None, status: str | None = None):
        self.get(key)
        if status is not None and status not in ('active', 'archived', 'deleted'):
            raise ValueError('Invalid conversation status.')
        with self.store.connect() as db:
            if title is not None:
                payload = self.cipher.seal(validate_private_text(title, 120), self.owner)
                db.execute('UPDATE conversations SET title=?,updated_at=?,revision=revision+1 WHERE id=? AND owner=?',
                           (payload, utc_now(), key, self.owner))
            if status is not None:
                db.execute('UPDATE conversations SET status=?,updated_at=?,revision=revision+1 WHERE id=? AND owner=?',
                           (status, utc_now(), key, self.owner))
            if status == 'deleted':
                db.execute('DELETE FROM messages WHERE conversation_id=? AND owner=?', (key, self.owner))
                db.execute('UPDATE conversations SET title=NULL WHERE id=? AND owner=?', (key, self.owner))

    def set_retention(self, days: int | None):
        if days is not None and (type(days) is not int or not 1 <= days <= 3650):
            raise ValueError('Retention must be 1–3650 days or disabled.')
        with self.store.connect() as db:
            db.execute('INSERT INTO conversation_preferences VALUES(?,?) '
                       'ON CONFLICT(owner) DO UPDATE SET retention_days=excluded.retention_days', (self.owner, days))

    def apply_sync(self, db, key, payload, deleted=False):
        """Caller owns reviewed conflict checks and the same SQLite transaction."""
        identifier(key)
        now = utc_now()
        db.execute('DELETE FROM messages WHERE conversation_id=? AND owner=?', (key, self.owner))
        if deleted:
            db.execute('UPDATE conversations SET title=NULL,status=?,revision=revision+1 WHERE id=? AND owner=?',
                       ('deleted', key, self.owner))
            return
        title = self.cipher.seal(validate_private_text(payload['title'], 120), self.owner)
        db.execute('INSERT INTO conversations(id,owner,title,created_at,updated_at,status) VALUES(?,?,?,?,?,?) '
                   'ON CONFLICT(id) DO UPDATE SET title=excluded.title,updated_at=excluded.updated_at,revision=conversations.revision+1',
                   (key, self.owner, title, now, now, 'active'))
        for message in payload['messages']:
            db.execute('INSERT INTO messages VALUES(?,?,?,?,?,?,?,?)', (str(uuid.uuid4()), key, self.owner, message['role'],
                self.cipher.seal(validate_private_text(message['content']), self.owner), now, message['provider'], message['model']))

    def purge_expired(self, cutoff: str):
        with self.store.connect() as db:
            ids = db.execute('SELECT id FROM conversations WHERE owner=? AND status<>? AND updated_at<?',
                             (self.owner, 'deleted', cutoff)).fetchall()
            for (key,) in ids:
                db.execute('DELETE FROM messages WHERE conversation_id=? AND owner=?', (key, self.owner))
                db.execute('UPDATE conversations SET title=NULL,status=?,revision=revision+1 WHERE id=? AND owner=?',
                           ('deleted', key, self.owner))
