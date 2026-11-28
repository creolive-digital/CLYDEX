"""Portable metadata generates reviewed T-SQL; ownership is enforced by composite FKs."""
from sqlalchemy import (MetaData, Table, Column, String, LargeBinary, Integer, BigInteger, Boolean,
                        ForeignKey, ForeignKeyConstraint, UniqueConstraint, CheckConstraint, Index)
from sqlalchemy.dialects.mssql import VARBINARY

metadata = MetaData(naming_convention={'ix': 'ix_%(table_name)s_%(column_0_name)s',
    'uq': 'uq_%(table_name)s_%(column_0_N_name)s', 'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s', 'ck': 'ck_%(table_name)s_%(constraint_name)s'})
UUID = String(36)
BLOB = LargeBinary().with_variant(VARBINARY(None), 'mssql')
TIME = BigInteger


accounts = Table('clx_accounts', metadata,
    Column('id', UUID, primary_key=True), Column('login_hash', String(64), nullable=False, unique=True),
    Column('profile', BLOB, nullable=False), Column('password_hash', String(256), nullable=False),
    Column('recovery_hash', String(64), nullable=False), Column('created_at', TIME, nullable=False),
    Column('disabled', Boolean, nullable=False), Column('used_bytes', TIME, nullable=False),
    Column('quota_bytes', TIME, nullable=False),
    CheckConstraint('used_bytes >= 0 AND used_bytes <= quota_bytes', name='quota'))
owner_keys = Table('clx_owner_keys', metadata, Column('owner_id', UUID, ForeignKey('clx_accounts.id'), primary_key=True),
    Column('wrapped_key', BLOB, nullable=False), Column('key_version', Integer, nullable=False))


def owned(name: str, *fields, constraints=()):
    return Table('clx_' + name, metadata, Column('id', UUID, primary_key=True),
        Column('owner_id', UUID, ForeignKey('clx_accounts.id'), nullable=False), *fields,
        UniqueConstraint('owner_id', 'id'), *constraints)


devices = owned('devices', Column('profile', BLOB, nullable=False), Column('scopes', String(400), nullable=False),
    Column('created_at', TIME, nullable=False), Column('last_seen', TIME, nullable=False),
    Column('revoked_at', TIME), Column('credential_version', Integer, nullable=False))
sessions = owned('sessions', Column('device_id', UUID), Column('access_hash', String(64), nullable=False),
    Column('refresh_hash', String(64), nullable=False), Column('scopes', String(400), nullable=False),
    Column('created_at', TIME, nullable=False), Column('access_expires', TIME, nullable=False),
    Column('refresh_expires', TIME, nullable=False), Column('generation', Integer, nullable=False),
    Column('revoked_at', TIME), constraints=(ForeignKeyConstraint(['owner_id', 'device_id'],
        ['clx_devices.owner_id', 'clx_devices.id']),))
refresh_uses = Table('clx_refresh_uses', metadata, Column('token_hash', String(64), primary_key=True),
    Column('session_id', UUID, ForeignKey('clx_sessions.id'), nullable=False),
    Column('used_at', TIME, nullable=False), Column('expires_at', TIME, nullable=False))
pairings = owned('pairings', Column('profile', BLOB, nullable=False), Column('scopes', String(400), nullable=False),
    Column('claim_hash', String(64), nullable=False, unique=True), Column('expires_at', TIME, nullable=False),
    Column('approved_at', TIME), Column('claimed_at', TIME))
collections = owned('collections', Column('profile', BLOB, nullable=False), Column('revision', Integer, nullable=False),
    Column('created_at', TIME, nullable=False), Column('deleted_at', TIME))
documents = owned('documents', Column('collection_id', UUID, nullable=False),
    Column('profile', BLOB, nullable=False), Column('current_version', Integer, nullable=False),
    Column('revision', Integer, nullable=False), Column('status', String(40), nullable=False),
    Column('created_at', TIME, nullable=False), Column('deleted_at', TIME),
    constraints=(ForeignKeyConstraint(['owner_id', 'collection_id'], ['clx_collections.owner_id', 'clx_collections.id']),))
versions = owned('document_versions', Column('document_id', UUID, nullable=False),
    Column('version', Integer, nullable=False), Column('object_id', UUID, nullable=False, unique=True),
    Column('sha256', String(64), nullable=False), Column('size_bytes', TIME, nullable=False),
    Column('created_at', TIME, nullable=False), Column('parser', String(60), nullable=False),
    Column('extraction', BLOB), constraints=(UniqueConstraint('owner_id', 'document_id', 'version'),
        ForeignKeyConstraint(['owner_id', 'document_id'], ['clx_documents.owner_id', 'clx_documents.id']),))
passages = owned('chunks', Column('document_id', UUID, nullable=False), Column('version', Integer, nullable=False),
    Column('ordinal', Integer, nullable=False), Column('payload', BLOB, nullable=False),
    constraints=(UniqueConstraint('owner_id', 'document_id', 'version', 'ordinal'),
        ForeignKeyConstraint(['owner_id', 'document_id'], ['clx_documents.owner_id', 'clx_documents.id']),))
chunk_terms = Table('clx_chunk_terms', metadata, Column('owner_id', UUID, primary_key=True),
    Column('term_hash', String(64), primary_key=True), Column('chunk_id', UUID, primary_key=True),
    ForeignKeyConstraint(['owner_id', 'chunk_id'], ['clx_chunks.owner_id', 'clx_chunks.id']))
embeddings = owned('embeddings', Column('chunk_id', UUID, nullable=False), Column('model', String(160), nullable=False),
    Column('model_revision', String(160), nullable=False), Column('dimensions', Integer, nullable=False),
    Column('payload', BLOB, nullable=False), Column('created_at', TIME, nullable=False),
    constraints=(ForeignKeyConstraint(['owner_id', 'chunk_id'], ['clx_chunks.owner_id', 'clx_chunks.id']),
        UniqueConstraint('owner_id', 'chunk_id', 'model', 'model_revision'),
        CheckConstraint('dimensions BETWEEN 1 AND 1998', name='vector_dimensions')))
entities = Table('clx_sync_entities', metadata, Column('owner_id', UUID, ForeignKey('clx_accounts.id'), primary_key=True),
    Column('category', String(20), primary_key=True), Column('entity_id', UUID, primary_key=True),
    Column('version', Integer, nullable=False), Column('payload', BLOB), Column('deleted', Boolean, nullable=False),
    Column('updated_at', TIME, nullable=False))
changes = Table('clx_changes', metadata, Column('sequence', BigInteger().with_variant(Integer, 'sqlite'),
    primary_key=True, autoincrement=True), Column('owner_id', UUID, ForeignKey('clx_accounts.id'), nullable=False),
    Column('category', String(20), nullable=False), Column('entity_id', UUID, nullable=False),
    Column('version', Integer, nullable=False), Column('deleted', Boolean, nullable=False),
    Column('payload', BLOB), Column('created_at', TIME, nullable=False))
operations = Table('clx_operations', metadata, Column('owner_id', UUID, ForeignKey('clx_accounts.id'), primary_key=True),
    Column('operation_id', UUID, primary_key=True), Column('digest', String(64), nullable=False),
    Column('result', BLOB, nullable=False), Column('created_at', TIME, nullable=False))
sync_state = Table('clx_sync_state', metadata, Column('owner_id', UUID, primary_key=True),
    Column('device_id', UUID, primary_key=True), Column('category', String(20), primary_key=True),
    Column('cursor', TIME, nullable=False), Column('updated_at', TIME, nullable=False),
    ForeignKeyConstraint(['owner_id', 'device_id'], ['clx_devices.owner_id', 'clx_devices.id']))
jobs = owned('jobs', Column('document_id', UUID, nullable=False), Column('version', Integer, nullable=False),
    Column('status', String(20), nullable=False), Column('error_code', String(80), nullable=False),
    Column('attempts', Integer, nullable=False), Column('lease_until', TIME), Column('created_at', TIME, nullable=False),
    constraints=(ForeignKeyConstraint(['owner_id', 'document_id'], ['clx_documents.owner_id', 'clx_documents.id']),))
audit = Table('clx_audit', metadata, Column('sequence', BigInteger().with_variant(Integer, 'sqlite'),
    primary_key=True, autoincrement=True), Column('owner_id', UUID, ForeignKey('clx_accounts.id')),
    Column('code', String(40), nullable=False), Column('object_id', UUID), Column('created_at', TIME, nullable=False))
backups = owned('backups', Column('sha256', String(64), nullable=False), Column('size_bytes', TIME, nullable=False),
    Column('created_at', TIME, nullable=False), Column('status', String(20), nullable=False))
schema_versions = Table('clx_schema_versions', metadata, Column('version', Integer, primary_key=True),
    Column('sha256', String(64), nullable=False), Column('applied_at', TIME, nullable=False))
garbage = Table('clx_storage_garbage', metadata, Column('owner_id', UUID, ForeignKey('clx_accounts.id'), primary_key=True),
    Column('object_id', UUID, primary_key=True), Column('size_bytes', TIME, nullable=False), Column('created_at', TIME, nullable=False))
invitation_uses = Table('clx_invitation_uses', metadata, Column('digest', String(64), primary_key=True),
    Column('used_at', TIME, nullable=False))
# These data categories remain distinct and encrypted, including their revision history.
memory_revisions = owned('memory_revisions', Column('entity_id', UUID, nullable=False),
    Column('version', Integer, nullable=False), Column('payload', BLOB), Column('deleted', Boolean, nullable=False),
    Column('created_at', TIME, nullable=False), constraints=(UniqueConstraint('owner_id', 'entity_id', 'version'),))
conversations = owned('conversations', Column('profile', BLOB, nullable=False),
    Column('revision', Integer, nullable=False), Column('deleted_at', TIME))
messages = owned('messages', Column('conversation_id', UUID, nullable=False), Column('payload', BLOB, nullable=False),
    Column('ordinal', Integer, nullable=False), constraints=(ForeignKeyConstraint(['owner_id', 'conversation_id'],
        ['clx_conversations.owner_id', 'clx_conversations.id']), UniqueConstraint('owner_id', 'conversation_id', 'ordinal')))
preferences = Table('clx_preferences', metadata, Column('owner_id', UUID, ForeignKey('clx_accounts.id'), primary_key=True),
    Column('category', String(20), primary_key=True), Column('payload', BLOB, nullable=False),
    Column('revision', Integer, nullable=False))

Index('ix_changes_owner_cursor', changes.c.owner_id, changes.c.sequence)
Index('ix_documents_owner_collection', documents.c.owner_id, documents.c.collection_id, documents.c.deleted_at)
Index('ix_jobs_status_lease', jobs.c.status, jobs.c.lease_until, jobs.c.created_at)
Index('ix_chunks_document_version', passages.c.owner_id, passages.c.document_id, passages.c.version)
Index('ix_sessions_owner_device', sessions.c.owner_id, sessions.c.device_id, sessions.c.revoked_at)
