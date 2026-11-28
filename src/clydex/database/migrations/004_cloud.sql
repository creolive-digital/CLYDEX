CREATE TABLE sync_state (
 owner TEXT NOT NULL, binding TEXT NOT NULL, cursor INTEGER NOT NULL DEFAULT 0,
 policy BLOB NOT NULL, PRIMARY KEY(owner,binding)
);
CREATE TABLE sync_outbox (
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, binding TEXT NOT NULL, category TEXT NOT NULL,
 entity_id TEXT NOT NULL, base_version INTEGER NOT NULL, payload BLOB NOT NULL,
 source_id TEXT NOT NULL, source_revision INTEGER NOT NULL, status TEXT NOT NULL,
 attempts INTEGER NOT NULL DEFAULT 0, next_attempt REAL NOT NULL DEFAULT 0, error TEXT NOT NULL DEFAULT ''
);
CREATE INDEX sync_outbox_owner ON sync_outbox(owner,binding,status,next_attempt);
CREATE TABLE sync_inbox (
 owner TEXT NOT NULL, binding TEXT NOT NULL, sequence INTEGER NOT NULL, category TEXT NOT NULL,
 entity_id TEXT NOT NULL, version INTEGER NOT NULL, deleted INTEGER NOT NULL, payload BLOB,
 PRIMARY KEY(owner,binding,sequence)
);
CREATE TABLE sync_links (
 owner TEXT NOT NULL, binding TEXT NOT NULL, category TEXT NOT NULL, entity_id TEXT NOT NULL,
 local_id TEXT NOT NULL, local_revision INTEGER NOT NULL, version INTEGER NOT NULL,
 PRIMARY KEY(owner,binding,category,entity_id)
);
CREATE TABLE sync_replicas (
 owner TEXT NOT NULL, binding TEXT NOT NULL, category TEXT NOT NULL, entity_id TEXT NOT NULL,
 payload BLOB, version INTEGER NOT NULL, deleted INTEGER NOT NULL,
 PRIMARY KEY(owner,binding,category,entity_id)
);
CREATE TABLE knowledge_cache (
 owner TEXT NOT NULL, binding TEXT NOT NULL, document_id TEXT NOT NULL, revision INTEGER NOT NULL,
 expires REAL NOT NULL, size_bytes INTEGER NOT NULL, payload BLOB NOT NULL,
 PRIMARY KEY(owner,binding,document_id)
);
PRAGMA user_version = 4;
