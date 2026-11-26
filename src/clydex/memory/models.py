"""Memory categories and provenance returned to the owning user."""
from dataclasses import dataclass


CATEGORIES = ('preferences', 'profile', 'projects', 'routines', 'work', 'facts')


@dataclass(frozen=True)
class Memory:
    id: str
    category: str
    value: str
    origin: str
    source_kind: str
    source_id: str
    confirmed: bool
    local_only: bool
    created_at: str
    updated_at: str
    revision: int
    status: str = 'active'
