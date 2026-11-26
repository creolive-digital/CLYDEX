"""Temporary/persistent session lifecycle. Only explicitly retained safe text is saved."""
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import json
import uuid

from clydex.conversations.models import Conversation, utc_now
from clydex.core.errors import PermissionDenied
from clydex.security.content import validate_private_text


class ConversationService:
    def __init__(self, repository):
        self.repository = repository
        now = utc_now()
        self.current = Conversation(str(uuid.uuid4()), 'Temporary conversation', True, now, now)
        self._temporary: list[dict] = []

    def new(self, title: str, persistent: bool, consent: bool = False) -> dict:
        if type(persistent) is not bool or (persistent and consent is not True):
            raise PermissionDenied('Persistent conversation needs explicit consent.')
        title = validate_private_text(title, 120)
        if persistent:
            conversation = self.repository.create(title)
        else:
            now = utc_now()
            conversation = Conversation(str(uuid.uuid4()), title, True, now, now)
        self.current, self._temporary = conversation, []
        return asdict(conversation)

    def resume(self, key: str) -> list[dict]:
        self.current = self.repository.get(key)
        self._temporary = []
        return self.repository.messages(key)

    def record(self, prompt: str, answer: str, provider: str = '', model: str = '', *, sensitive: bool = False) -> bool:
        if sensitive:
            return False
        try:
            validate_private_text(prompt)
            validate_private_text(answer)
        except (PermissionDenied, ValueError):
            return False
        if not self.current.temporary:
            self.repository.append_pair(self.current.id, prompt, answer, provider, model)
        else:
            now = utc_now()
            self._temporary.extend(dict(role=r, content=t, provider=provider, model=model, created_at=now)
                                   for r, t in (('user', prompt), ('assistant', answer)))
            self._temporary = self._temporary[-100:]
        self.current = replace(self.current, updated_at=utc_now())
        return True

    def export(self, key: str | None = None) -> str:
        conversation = self.current if key is None else self.repository.get(key)
        messages = self._temporary if conversation.temporary else self.repository.export_messages(conversation.id)
        return json.dumps({'version': 1, 'conversation': asdict(conversation), 'messages': messages}, ensure_ascii=False, indent=2)

    def purge_expired(self):
        with self.repository.store.connect() as db:
            row = db.execute('SELECT retention_days FROM conversation_preferences WHERE owner=?',
                             (self.repository.owner,)).fetchone()
        if row and row[0]:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=row[0])).isoformat(timespec='microseconds')
            self.repository.purge_expired(cutoff)
            if not self.current.temporary:
                try:
                    self.repository.get(self.current.id)
                except PermissionDenied:
                    self.new('Temporary conversation', False)
