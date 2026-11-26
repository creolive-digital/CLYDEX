"""Typed data compartments. None of their contents can grant tool permissions."""
from dataclasses import dataclass, replace
import json

from clydex.core.contracts import canonical_json


@dataclass(frozen=True)
class ContextBundle:
    prompt: str
    history_json: str = '[]'
    memory_json: str = '[]'
    knowledge_json: str = '[]'
    tool_results_json: str = '{}'
    external_json: str = '[]'
    local_only: bool = False

    @classmethod
    def from_legacy(cls, data: dict, memories: list | None = None, local_only: bool = False):
        # Everything except the current prompt/history is classified conservatively.
        extra = {key: value for key, value in data.items()
                 if key not in ('request', 'history', 'has_inbox_snapshot')}
        if data.get('has_inbox_snapshot'):
            extra['has_inbox_snapshot'] = True
        return cls(str(data.get('request', '')), canonical_json(data.get('history', [])),
                   canonical_json(memories or []), tool_results_json=canonical_json(extra),
                   local_only=local_only)

    @property
    def private(self) -> bool:
        return (self.history_json != '[]' or self.memory_json != '[]' or self.knowledge_json != '[]'
                or self.tool_results_json != '{}' or self.external_json != '[]')

    def data(self) -> dict:
        return {'current_user_prompt': self.prompt, 'conversation_history': json.loads(self.history_json),
                'personal_memory': json.loads(self.memory_json), 'retrieved_knowledge': json.loads(self.knowledge_json),
                'sensitive_tool_results': json.loads(self.tool_results_json),
                'external_document_content': json.loads(self.external_json)}

    def for_provider(self, local: bool) -> 'ContextBundle':
        memories = json.loads(self.memory_json)
        if not local:
            memories = [record for record in memories if not record.get('local_only', True)]
        return replace(self, memory_json=canonical_json(memories))
