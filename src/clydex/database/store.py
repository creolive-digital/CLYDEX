"""Short-lived connections, transactional migrations and allowlisted metadata."""
from importlib.resources import files
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import threading


class LocalStore:
    SCHEMA_VERSION = 5
    MIGRATIONS = ('001_foundation.sql', '002_conversations.sql', '003_memory.sql', '004_cloud.sql',
                  '005_operating.sql')
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            if version > self.SCHEMA_VERSION:
                raise RuntimeError('Database is newer than this application. Downgrade refused.')
            for migration in self.MIGRATIONS[version:]:
                script = files('clydex.database').joinpath('migrations/' + migration).read_text('utf-8')
                try:
                    for statement in script.split(';'):
                        if statement.strip():
                            connection.execute(statement)
                except Exception:
                    connection.rollback()
                    raise

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA busy_timeout=5000')
        connection.execute('PRAGMA secure_delete=ON')
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def get_setting(self, key: str):
        self._validate_setting(key)
        with self._lock, self.connect() as connection:
            row = connection.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    @staticmethod
    def _validate_setting(key: str, value=None, write: bool = False) -> None:
        if key not in ('recognition_mode', 'speak_replies'):
            raise ValueError('Only non-secret voice preferences are stored here.')
        if write and ((key == 'recognition_mode' and value not in ('en', 'en-accurate', 'auto'))
                      or (key == 'speak_replies' and type(value) is not bool)):
            raise ValueError('Invalid setting.')

    def set_setting(self, key: str, value) -> None:
        self._validate_setting(key, value, True)
        with self._lock, self.connect() as connection:
            connection.execute('INSERT INTO settings(key,value) VALUES(?,?) '
                               'ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                               (key, json.dumps(value)))

    def audit(self, action_id: str, tool: str, outcome: str) -> None:
        from clydex.security.permissions import TOOL_SPECS
        if (len(action_id) != 64 or any(c not in '0123456789abcdef' for c in action_id)
                or tool not in {spec.name for spec in TOOL_SPECS} | {'unknown'}
                or outcome not in ('requested', 'approved', 'denied', 'executed', 'failed', 'cancelled')):
            raise ValueError('Audit metadata is not allowlisted.')
        with self._lock, self.connect() as connection:
            connection.execute('INSERT INTO audit_events(action_id,tool,outcome) VALUES(?,?,?)',
                               (action_id, tool, outcome))
