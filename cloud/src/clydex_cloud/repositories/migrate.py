"""Operator-only transactional migrations; never called by application startup."""
import hashlib
from importlib.resources import files
import time

from sqlalchemy import inspect, insert, text
from clydex_cloud.repositories.schema import metadata, schema_versions


def script(name='001_core.sql'):
    return files('clydex_cloud.repositories').joinpath('migrations/' + name).read_text('utf-8').replace('\r\n', '\n')


def migration_hash():
    return hashlib.sha256(script().encode()).hexdigest()


def migrate(database):
    with database.transaction() as connection:
        if inspect(connection).has_table(schema_versions.name):
            rows = connection.execute(schema_versions.select()).mappings().all()
            if len(rows) == 1 and rows[0]['version'] == 1 and rows[0]['sha256'] == migration_hash():
                return False
            raise ValueError('Migration checksum/version mismatch; recovery review required.')
        if any(name.startswith('clx_') for name in inspect(connection).get_table_names()):
            raise ValueError('A partial schema requires reviewed recovery, not overwrite.')
        if database.simulated:
            metadata.create_all(connection)
        else:
            for statement in script().split('\nGO\n'):
                if statement.strip():
                    connection.exec_driver_sql(statement)
        connection.execute(insert(schema_versions).values(version=1, sha256=migration_hash(), applied_at=int(time.time())))
        return True


def rollback_empty(database):
    """Destructive downgrade is refused when ANY business row exists."""
    with database.transaction() as connection:
        for table in metadata.sorted_tables:
            if table is not schema_versions and connection.execute(table.select().limit(1)).first():
                raise ValueError('Populated schema rollback refused. Restore a validated recovery export instead.')
        if database.simulated:
            metadata.drop_all(connection)
        else:
            for statement in script('001_core.down.sql').split('\nGO\n'):
                if statement.strip():
                    connection.execute(text(statement))
