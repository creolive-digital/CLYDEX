CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    action_id TEXT NOT NULL,
    tool TEXT NOT NULL,
    outcome TEXT NOT NULL
);
PRAGMA user_version = 1;
