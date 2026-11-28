CREATE TABLE operating_records (
    owner TEXT NOT NULL,
    category TEXT NOT NULL,
    id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK(revision > 0),
    payload BLOB NOT NULL,
    PRIMARY KEY(owner, category, id)
);
CREATE TABLE workflow_versions (
    owner TEXT NOT NULL,
    id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    payload BLOB NOT NULL,
    PRIMARY KEY(owner, id, revision)
);
CREATE TABLE workflow_runs (
    owner TEXT NOT NULL,
    id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('running','complete','failed','cancelled','interrupted')),
    started_at REAL NOT NULL,
    finished_at REAL,
    nodes BLOB NOT NULL,
    PRIMARY KEY(owner, id)
);
CREATE INDEX ix_workflow_runs_owner ON workflow_runs(owner, started_at);
CREATE TABLE trigger_receipts (
    owner TEXT NOT NULL,
    trigger_id TEXT NOT NULL,
    event_digest TEXT NOT NULL,
    expires_at REAL NOT NULL,
    PRIMARY KEY(owner, trigger_id, event_digest)
);
PRAGMA user_version=5;
