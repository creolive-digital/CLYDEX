"""Response validation filters implementation/private fields from HTTP output."""
from pydantic import BaseModel, ConfigDict, Field


class Response(BaseModel):
    model_config = ConfigDict(extra='ignore', strict=True)


class Status(Response):
    status: str


class ErrorDetail(Response):
    code: str
    request_id: str
    current_version: int | None = None
    retry_after: int | None = None
    fields: list[dict] | None = None


class ErrorEnvelope(Response):
    error: ErrorDetail


class Account(Response):
    id: str
    login: str


class Capabilities(Response):
    database: str
    embedding_configured: bool
    vector_strategy: str
    preview_vector_indexes: bool
    formats: str
    server_managed_encryption: bool
    e2ee: bool


class Session(Response):
    access_token: str
    refresh_token: str
    expires_in: int
    account_id: str
    device_id: str | None
    scopes: list[str]


class Provisioned(Response):
    account_id: str
    recovery_code: str


class Recovered(Response):
    recovered: bool
    recovery_code: str


class Flag(Response):
    revoked: bool | None = None
    approved: bool | None = None
    deleted: bool | None = None


class Items(Response):
    items: list[dict] = Field(max_length=500)
    truncated: bool = False


class PairingResult(Response):
    id: str
    pairing_token: str
    expires_in: int
    approved: bool


class CollectionResult(Response):
    id: str
    revision: int
    title: str
    description: str


class UploadResult(Response):
    document_id: str
    duplicate: bool
    version: int | None = None
    revision: int | None = None
    job_id: str | None = None


class JobResult(Response):
    job_id: str
    status: str


class Citation(Response):
    citation_id: str
    document_id: str
    version: int
    revision: int
    ordinal: int
    name: str
    location: str
    excerpt: str
    collection_id: str | None = None
    title: str = ''
    score: float | None = None


class SearchResult(Response):
    items: list[Citation] = Field(max_length=20)
    mode: str
    insufficient_evidence: bool
    semantic_strategy: str | None = None


class SyncResult(Response):
    results: list[dict] = Field(max_length=20)


class Changes(Response):
    changes: list[dict] = Field(max_length=500)
    cursor: int
    has_more: bool


class Usage(Response):
    document_bytes: int
    quota_bytes: int
    pending_delete_bytes: int
