CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    category TEXT NOT NULL,
    content BLOB,
    origin TEXT NOT NULL CHECK(origin IN ('explicit','inferred')),
    source_kind TEXT NOT NULL,
    source_id TEXT NOT NULL,
    confirmed INTEGER NOT NULL CHECK(confirmed IN (0,1)),
    local_only INTEGER NOT NULL CHECK(local_only IN (0,1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active','deleted')),
    revision INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX memories_owner_category ON memories(owner, category, status);
CREATE TABLE memory_preferences (
    owner TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 1,
    automatic INTEGER NOT NULL DEFAULT 0,
    categories TEXT NOT NULL DEFAULT '[]'
);
PRAGMA user_version = 3;
