"""Manual memory and opt-in literal suggestions, always reviewed before saving."""
import json
import re
import uuid

from clydex.core.errors import PermissionDenied
from clydex.memory.models import CATEGORIES
from clydex.memory.retrieval import retrieve
from clydex.security.content import validate_private_text


class MemoryService:
    def __init__(self, repository):
        self.repository = repository
        self.pending: dict[str, dict] = {}

    def policy(self) -> dict:
        with self.repository.store.connect() as db:
            row = db.execute('SELECT enabled,automatic,categories FROM memory_preferences WHERE owner=?',
                             (self.repository.owner,)).fetchone()
        return dict(enabled=bool(row[0]), automatic=bool(row[1]), categories=json.loads(row[2])) if row else dict(
            enabled=True, automatic=False, categories=[])

    def configure(self, enabled: bool, automatic: bool, categories: list, consent: bool):
        if (type(enabled) is not bool or type(automatic) is not bool or type(consent) is not bool
                or not isinstance(categories, list) or any(c not in CATEGORIES for c in categories)):
            raise ValueError('Invalid memory permissions.')
        if automatic and (not enabled or consent is not True or not categories):
            raise PermissionDenied('Automatic suggestions require explicit opt-in and category selection.')
        with self.repository.store.connect() as db:
            db.execute('INSERT INTO memory_preferences VALUES(?,?,?,?) ON CONFLICT(owner) DO UPDATE SET '
                       'enabled=excluded.enabled,automatic=excluded.automatic,categories=excluded.categories',
                       (self.repository.owner, int(enabled), int(automatic), json.dumps(sorted(set(categories)))))
        if not automatic or not enabled:
            self.pending.clear()

    def remember(self, category: str, value: str, *, consent: bool, local_only: bool = True,
                 origin='explicit', source_kind='manual_ui', source_id='') -> dict:
        if consent is not True or not self.policy()['enabled']:
            raise PermissionDenied('Memory is disabled or consent is absent.')
        return self.repository.add(category, value, origin=origin, source_kind=source_kind,
                                   source_id=source_id, confirmed=True, local_only=local_only)

    def relevant(self, query: str) -> list[dict]:
        if not self.policy()['enabled']:
            return []
        return retrieve(self.repository.list(), query)

    def suggest(self, prompt: str, source_id: str, *, sensitive: bool = False) -> dict | None:
        policy = self.policy()
        if sensitive or not policy['enabled'] or not policy['automatic'] or len(prompt) > 500:
            return None
        patterns = {'preferences': r'I prefer .+', 'profile': r'My name is .+',
                    'projects': r'I am working on .+', 'routines': r'I usually .+',
                    'work': r'At work, .+', 'facts': r'A fact about me is .+'}
        for category in policy['categories']:
            if re.fullmatch(patterns[category], prompt.strip(), re.IGNORECASE):
                try:
                    validate_private_text(prompt, 500)
                except (PermissionDenied, ValueError):
                    return None
                proposal = dict(id=str(uuid.uuid4()), category=category, value=prompt.strip(),
                                source_id=source_id, origin='inferred')
                if len(self.pending) >= 20:
                    self.pending.pop(next(iter(self.pending)))
                self.pending[proposal['id']] = proposal
                return dict(proposal)
        return None

    def accept(self, key: str, *, consent: bool, local_only: bool = True) -> dict:
        proposal = self.pending.get(key)
        if proposal is None or not self.policy()['automatic']:
            raise PermissionDenied('Memory proposal expired or collection is disabled.')
        result = self.remember(proposal['category'], proposal['value'], consent=consent, local_only=local_only,
                               origin='inferred', source_kind='user_prompt', source_id=proposal['source_id'])
        self.pending.pop(key, None)
        return result
