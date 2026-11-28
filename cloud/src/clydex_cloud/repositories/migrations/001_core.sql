-- Generated SQL Server 2025 schema. Apply using clydex_cloud CLI only.
CREATE TABLE clx_accounts (
	id VARCHAR(36) NOT NULL,
	login_hash VARCHAR(64) NOT NULL,
	profile VARBINARY(max) NOT NULL,
	password_hash VARCHAR(256) NOT NULL,
	recovery_hash VARCHAR(64) NOT NULL,
	created_at BIGINT NOT NULL,
	disabled BIT NOT NULL,
	used_bytes BIGINT NOT NULL,
	quota_bytes BIGINT NOT NULL,
	CONSTRAINT pk_clx_accounts PRIMARY KEY (id),
	CONSTRAINT ck_clx_accounts_quota CHECK (used_bytes >= 0 AND used_bytes <= quota_bytes),
	CONSTRAINT uq_clx_accounts_login_hash UNIQUE (login_hash)
)
GO
CREATE TABLE clx_invitation_uses (
	digest VARCHAR(64) NOT NULL,
	used_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_invitation_uses PRIMARY KEY (digest)
)
GO
CREATE TABLE clx_schema_versions (
	version INTEGER NOT NULL IDENTITY,
	sha256 VARCHAR(64) NOT NULL,
	applied_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_schema_versions PRIMARY KEY (version)
)
GO
CREATE TABLE clx_audit (
	sequence BIGINT NOT NULL IDENTITY,
	owner_id VARCHAR(36) NULL,
	code VARCHAR(40) NOT NULL,
	object_id VARCHAR(36) NULL,
	created_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_audit PRIMARY KEY (sequence),
	CONSTRAINT fk_clx_audit_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_backups (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	sha256 VARCHAR(64) NOT NULL,
	size_bytes BIGINT NOT NULL,
	created_at BIGINT NOT NULL,
	status VARCHAR(20) NOT NULL,
	CONSTRAINT pk_clx_backups PRIMARY KEY (id),
	CONSTRAINT uq_clx_backups_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_backups_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_changes (
	sequence BIGINT NOT NULL IDENTITY,
	owner_id VARCHAR(36) NOT NULL,
	category VARCHAR(20) NOT NULL,
	entity_id VARCHAR(36) NOT NULL,
	version INTEGER NOT NULL,
	deleted BIT NOT NULL,
	payload VARBINARY(max) NULL,
	created_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_changes PRIMARY KEY (sequence),
	CONSTRAINT fk_clx_changes_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_collections (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	profile VARBINARY(max) NOT NULL,
	revision INTEGER NOT NULL,
	created_at BIGINT NOT NULL,
	deleted_at BIGINT NULL,
	CONSTRAINT pk_clx_collections PRIMARY KEY (id),
	CONSTRAINT uq_clx_collections_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_collections_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_conversations (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	profile VARBINARY(max) NOT NULL,
	revision INTEGER NOT NULL,
	deleted_at BIGINT NULL,
	CONSTRAINT pk_clx_conversations PRIMARY KEY (id),
	CONSTRAINT uq_clx_conversations_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_conversations_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_devices (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	profile VARBINARY(max) NOT NULL,
	scopes VARCHAR(400) NOT NULL,
	created_at BIGINT NOT NULL,
	last_seen BIGINT NOT NULL,
	revoked_at BIGINT NULL,
	credential_version INTEGER NOT NULL,
	CONSTRAINT pk_clx_devices PRIMARY KEY (id),
	CONSTRAINT uq_clx_devices_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_devices_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_memory_revisions (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	entity_id VARCHAR(36) NOT NULL,
	version INTEGER NOT NULL,
	payload VARBINARY(max) NULL,
	deleted BIT NOT NULL,
	created_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_memory_revisions PRIMARY KEY (id),
	CONSTRAINT uq_clx_memory_revisions_owner_id_entity_id_version UNIQUE (owner_id, entity_id, version),
	CONSTRAINT uq_clx_memory_revisions_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_memory_revisions_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_operations (
	owner_id VARCHAR(36) NOT NULL,
	operation_id VARCHAR(36) NOT NULL,
	digest VARCHAR(64) NOT NULL,
	result VARBINARY(max) NOT NULL,
	created_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_operations PRIMARY KEY (owner_id, operation_id),
	CONSTRAINT fk_clx_operations_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_owner_keys (
	owner_id VARCHAR(36) NOT NULL,
	wrapped_key VARBINARY(max) NOT NULL,
	key_version INTEGER NOT NULL,
	CONSTRAINT pk_clx_owner_keys PRIMARY KEY (owner_id),
	CONSTRAINT fk_clx_owner_keys_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_pairings (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	profile VARBINARY(max) NOT NULL,
	scopes VARCHAR(400) NOT NULL,
	claim_hash VARCHAR(64) NOT NULL,
	expires_at BIGINT NOT NULL,
	approved_at BIGINT NULL,
	claimed_at BIGINT NULL,
	CONSTRAINT pk_clx_pairings PRIMARY KEY (id),
	CONSTRAINT uq_clx_pairings_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_pairings_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id),
	CONSTRAINT uq_clx_pairings_claim_hash UNIQUE (claim_hash)
)
GO
CREATE TABLE clx_preferences (
	owner_id VARCHAR(36) NOT NULL,
	category VARCHAR(20) NOT NULL,
	payload VARBINARY(max) NOT NULL,
	revision INTEGER NOT NULL,
	CONSTRAINT pk_clx_preferences PRIMARY KEY (owner_id, category),
	CONSTRAINT fk_clx_preferences_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_storage_garbage (
	owner_id VARCHAR(36) NOT NULL,
	object_id VARCHAR(36) NOT NULL,
	size_bytes BIGINT NOT NULL,
	created_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_storage_garbage PRIMARY KEY (owner_id, object_id),
	CONSTRAINT fk_clx_storage_garbage_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_sync_entities (
	owner_id VARCHAR(36) NOT NULL,
	category VARCHAR(20) NOT NULL,
	entity_id VARCHAR(36) NOT NULL,
	version INTEGER NOT NULL,
	payload VARBINARY(max) NULL,
	deleted BIT NOT NULL,
	updated_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_sync_entities PRIMARY KEY (owner_id, category, entity_id),
	CONSTRAINT fk_clx_sync_entities_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_documents (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	collection_id VARCHAR(36) NOT NULL,
	profile VARBINARY(max) NOT NULL,
	current_version INTEGER NOT NULL,
	revision INTEGER NOT NULL,
	status VARCHAR(40) NOT NULL,
	created_at BIGINT NOT NULL,
	deleted_at BIGINT NULL,
	CONSTRAINT pk_clx_documents PRIMARY KEY (id),
	CONSTRAINT fk_clx_documents_owner_id_clx_collections FOREIGN KEY(owner_id, collection_id) REFERENCES clx_collections (owner_id, id),
	CONSTRAINT uq_clx_documents_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_documents_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_messages (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	conversation_id VARCHAR(36) NOT NULL,
	payload VARBINARY(max) NOT NULL,
	ordinal INTEGER NOT NULL,
	CONSTRAINT pk_clx_messages PRIMARY KEY (id),
	CONSTRAINT fk_clx_messages_owner_id_clx_conversations FOREIGN KEY(owner_id, conversation_id) REFERENCES clx_conversations (owner_id, id),
	CONSTRAINT uq_clx_messages_owner_id_conversation_id_ordinal UNIQUE (owner_id, conversation_id, ordinal),
	CONSTRAINT uq_clx_messages_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_messages_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_sessions (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	device_id VARCHAR(36) NULL,
	access_hash VARCHAR(64) NOT NULL,
	refresh_hash VARCHAR(64) NOT NULL,
	scopes VARCHAR(400) NOT NULL,
	created_at BIGINT NOT NULL,
	access_expires BIGINT NOT NULL,
	refresh_expires BIGINT NOT NULL,
	generation INTEGER NOT NULL,
	revoked_at BIGINT NULL,
	CONSTRAINT pk_clx_sessions PRIMARY KEY (id),
	CONSTRAINT fk_clx_sessions_owner_id_clx_devices FOREIGN KEY(owner_id, device_id) REFERENCES clx_devices (owner_id, id),
	CONSTRAINT uq_clx_sessions_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_sessions_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_sync_state (
	owner_id VARCHAR(36) NOT NULL,
	device_id VARCHAR(36) NOT NULL,
	category VARCHAR(20) NOT NULL,
	[cursor] BIGINT NOT NULL,
	updated_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_sync_state PRIMARY KEY (owner_id, device_id, category),
	CONSTRAINT fk_clx_sync_state_owner_id_clx_devices FOREIGN KEY(owner_id, device_id) REFERENCES clx_devices (owner_id, id)
)
GO
CREATE TABLE clx_chunks (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	document_id VARCHAR(36) NOT NULL,
	version INTEGER NOT NULL,
	ordinal INTEGER NOT NULL,
	payload VARBINARY(max) NOT NULL,
	CONSTRAINT pk_clx_chunks PRIMARY KEY (id),
	CONSTRAINT uq_clx_chunks_owner_id_document_id_version_ordinal UNIQUE (owner_id, document_id, version, ordinal),
	CONSTRAINT fk_clx_chunks_owner_id_clx_documents FOREIGN KEY(owner_id, document_id) REFERENCES clx_documents (owner_id, id),
	CONSTRAINT uq_clx_chunks_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_chunks_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_document_versions (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	document_id VARCHAR(36) NOT NULL,
	version INTEGER NOT NULL,
	object_id VARCHAR(36) NOT NULL,
	sha256 VARCHAR(64) NOT NULL,
	size_bytes BIGINT NOT NULL,
	created_at BIGINT NOT NULL,
	parser VARCHAR(60) NOT NULL,
	extraction VARBINARY(max) NULL,
	CONSTRAINT pk_clx_document_versions PRIMARY KEY (id),
	CONSTRAINT uq_clx_document_versions_owner_id_document_id_version UNIQUE (owner_id, document_id, version),
	CONSTRAINT fk_clx_document_versions_owner_id_clx_documents FOREIGN KEY(owner_id, document_id) REFERENCES clx_documents (owner_id, id),
	CONSTRAINT uq_clx_document_versions_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_document_versions_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id),
	CONSTRAINT uq_clx_document_versions_object_id UNIQUE (object_id)
)
GO
CREATE TABLE clx_jobs (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	document_id VARCHAR(36) NOT NULL,
	version INTEGER NOT NULL,
	status VARCHAR(20) NOT NULL,
	error_code VARCHAR(80) NOT NULL,
	attempts INTEGER NOT NULL,
	lease_until BIGINT NULL,
	created_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_jobs PRIMARY KEY (id),
	CONSTRAINT fk_clx_jobs_owner_id_clx_documents FOREIGN KEY(owner_id, document_id) REFERENCES clx_documents (owner_id, id),
	CONSTRAINT uq_clx_jobs_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_jobs_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE TABLE clx_refresh_uses (
	token_hash VARCHAR(64) NOT NULL,
	session_id VARCHAR(36) NOT NULL,
	used_at BIGINT NOT NULL,
	expires_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_refresh_uses PRIMARY KEY (token_hash),
	CONSTRAINT fk_clx_refresh_uses_session_id_clx_sessions FOREIGN KEY(session_id) REFERENCES clx_sessions (id)
)
GO
CREATE TABLE clx_chunk_terms (
	owner_id VARCHAR(36) NOT NULL,
	term_hash VARCHAR(64) NOT NULL,
	chunk_id VARCHAR(36) NOT NULL,
	CONSTRAINT pk_clx_chunk_terms PRIMARY KEY (owner_id, term_hash, chunk_id),
	CONSTRAINT fk_clx_chunk_terms_owner_id_clx_chunks FOREIGN KEY(owner_id, chunk_id) REFERENCES clx_chunks (owner_id, id)
)
GO
CREATE TABLE clx_embeddings (
	id VARCHAR(36) NOT NULL,
	owner_id VARCHAR(36) NOT NULL,
	chunk_id VARCHAR(36) NOT NULL,
	model VARCHAR(160) NOT NULL,
	model_revision VARCHAR(160) NOT NULL,
	dimensions INTEGER NOT NULL,
	payload VARBINARY(max) NOT NULL,
	created_at BIGINT NOT NULL,
	CONSTRAINT pk_clx_embeddings PRIMARY KEY (id),
	CONSTRAINT fk_clx_embeddings_owner_id_clx_chunks FOREIGN KEY(owner_id, chunk_id) REFERENCES clx_chunks (owner_id, id),
	CONSTRAINT uq_clx_embeddings_owner_id_chunk_id_model_model_revision UNIQUE (owner_id, chunk_id, model, model_revision),
	CONSTRAINT ck_clx_embeddings_vector_dimensions CHECK (dimensions BETWEEN 1 AND 1998),
	CONSTRAINT uq_clx_embeddings_owner_id_id UNIQUE (owner_id, id),
	CONSTRAINT fk_clx_embeddings_owner_id_clx_accounts FOREIGN KEY(owner_id) REFERENCES clx_accounts (id)
)
GO
CREATE INDEX ix_changes_owner_cursor ON clx_changes (owner_id, sequence)
GO
CREATE INDEX ix_documents_owner_collection ON clx_documents (owner_id, collection_id, deleted_at)
GO
CREATE INDEX ix_sessions_owner_device ON clx_sessions (owner_id, device_id, revoked_at)
GO
CREATE INDEX ix_chunks_document_version ON clx_chunks (owner_id, document_id, version)
GO
CREATE INDEX ix_jobs_status_lease ON clx_jobs (status, lease_until, created_at)
