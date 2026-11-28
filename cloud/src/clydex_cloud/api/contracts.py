"""Authoritative request contracts. OpenAPI is generated from these models/routes."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints

Identifier = Annotated[str, StringConstraints(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')]
Category = Literal['knowledge', 'memory', 'history', 'preferences', 'workflows', 'devices', 'themes']


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Register(Contract):
    login: str = Field(min_length=3, max_length=160)
    password: SecretStr = Field(min_length=12, max_length=256)
    invitation: SecretStr = Field(min_length=32, max_length=256)


class Login(Contract):
    login: str = Field(min_length=3, max_length=160)
    password: SecretStr = Field(min_length=1, max_length=256)


class Refresh(Contract):
    refresh_token: SecretStr = Field(min_length=40, max_length=256)


class Recover(Contract):
    login: str = Field(min_length=3, max_length=160)
    recovery_code: SecretStr = Field(min_length=40, max_length=256)
    new_password: SecretStr = Field(min_length=12, max_length=256)


class Pairing(Contract):
    display_name: str = Field(min_length=1, max_length=80)
    platform: str = Field(min_length=1, max_length=40)
    scopes: list[Literal['vault.read', 'vault.write', 'sync.read', 'sync.write']] = Field(min_length=1, max_length=4)


class Claim(Contract):
    pairing_token: SecretStr = Field(min_length=40, max_length=256)


class Collection(Contract):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default='', max_length=1000)


class Note(Contract):
    collection_id: Identifier
    title: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=1, max_length=64000)
    operation_id: Identifier


class Search(Contract):
    query: str = Field(min_length=1, max_length=1000)
    collection_id: Identifier | None = None
    mode: Literal['keyword', 'semantic'] = 'keyword'
    limit: int = Field(default=5, ge=1, le=20)


class SyncOperation(Contract):
    operation_id: Identifier
    category: Category
    entity_id: Identifier
    base_version: int = Field(ge=0, le=2147483646)
    deleted: bool = False
    payload: dict = Field(default_factory=dict)


class SyncBatch(Contract):
    operations: list[SyncOperation] = Field(min_length=1, max_length=20)


class SyncPreferences(Contract):
    knowledge: bool = False
    memory: bool = False
    history: bool = False
    preferences: bool = False
    workflows: bool = False
    devices: bool = False
    themes: bool = False
