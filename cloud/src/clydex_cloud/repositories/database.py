"""SQL Server-only production engine. Schema creation is never automatic at startup."""
from contextlib import contextmanager
import threading
from sqlalchemy import create_engine, select, text, event
from sqlalchemy.engine import make_url

from clydex_cloud.repositories.schema import schema_versions


class Database:
    def __init__(self, url: str, *, engine=None, test_only=False):
        if engine is not None:
            if not test_only:
                raise ValueError('Injected engines are test-only.')
            self.engine, self.simulated = engine, True
        else:
            parsed = make_url(url)
            query = {k.casefold(): v for k, v in parsed.query.items()}
            if (parsed.drivername != 'mssql+pyodbc' or len(query) != len(parsed.query)
                    or 'odbc_connect' in query or query.get('driver') != 'ODBC Driver 18 for SQL Server'
                    or str(query.get('encrypt', '')).lower() not in ('yes', 'strict')
                    or str(query.get('trustservercertificate', '')).lower() != 'no'):
                raise ValueError('Production requires SQL Server over verified TLS.')
            self.engine = create_engine(url, pool_size=4, max_overflow=0, pool_timeout=5,
                pool_pre_ping=True, hide_parameters=True, connect_args={'timeout': 5})
            @event.listens_for(self.engine, 'connect')
            def query_timeout(connection, record):
                connection.timeout = 15
            self.simulated = False
        self._test_lock = threading.RLock()

    @contextmanager
    def transaction(self):
        # The simulated StaticPool is one connection, not proof of SQL Server's
        # transactional isolation. Native production transactions use SQL locks.
        with self._test_lock if self.simulated else _NoLock(), self.engine.connect() as connection:
            if not self.simulated:
                connection = connection.execution_options(isolation_level='SERIALIZABLE')
            with connection.begin():
                if not self.simulated and int(connection.execute(text(
                        "SELECT SERVERPROPERTY('ProductMajorVersion')")).scalar()) != 17:
                    raise ValueError('The approved baseline requires SQL Server 2025 (17.x).')
                if not self.simulated:
                    connection.exec_driver_sql('SET LOCK_TIMEOUT 5000')
                yield connection

    def ready(self) -> bool:
        try:
            with self.engine.connect() as connection:
                if not self.simulated:
                    if int(connection.execute(text("SELECT SERVERPROPERTY('ProductMajorVersion')")).scalar()) != 17:
                        return False
                    from clydex_cloud.repositories.migrate import migration_hash
                    row = connection.execute(select(schema_versions)).mappings().one_or_none()
                    return bool(row and row['version'] == 1 and row['sha256'] == migration_hash())
                return connection.execute(select(schema_versions.c.version)).scalar() == 1
        except Exception:
            return False

    def close(self) -> None:
        self.engine.dispose()


class _NoLock:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
