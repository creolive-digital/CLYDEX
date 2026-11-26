"""Conversation model and validation shared by the local repository/service."""
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def identifier(value: str) -> str:
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ValueError('Invalid record identifier.')
    return value


@dataclass(frozen=True)
class Conversation:
    id: str
    title: str
    temporary: bool
    created_at: str
    updated_at: str
    status: str = 'active'
