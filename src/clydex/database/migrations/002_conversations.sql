CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    title BLOB,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active','archived','deleted')),
    revision INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX conversations_owner_time ON conversations(owner, updated_at);
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    owner TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
    content BLOB NOT NULL,
    created_at TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL
);
CREATE INDEX messages_session_time ON messages(owner, conversation_id, created_at);
CREATE TABLE conversation_preferences (
    owner TEXT PRIMARY KEY,
    retention_days INTEGER CHECK(retention_days IS NULL OR retention_days BETWEEN 1 AND 3650)
);
PRAGMA user_version = 2;
