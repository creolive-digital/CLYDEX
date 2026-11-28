"""Local operator tools. Never a public API and never automatic on startup."""
import argparse
import getpass
import os
from pathlib import Path
from clydex_cloud.core.config import Settings
from clydex_cloud.core.runtime import Runtime
from clydex_cloud.repositories.database import Database
from clydex_cloud.repositories.migrate import migrate, rollback_empty


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('keys', 'migrate', 'rollback-empty', 'provision', 'worker', 'backup', 'restore'))
    parser.add_argument('--file', type=Path)
    args = parser.parse_args()
    settings = Settings.from_environment()
    if args.operation == 'keys':
        settings.secrets_root.mkdir(parents=True, mode=0o700, exist_ok=True)
        for name in ('master.key', 'auth.key'):
            descriptor = os.open(settings.secrets_root / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'wb') as f:
                f.write(os.urandom(32))
        return
    if args.operation in ('migrate', 'rollback-empty', 'restore'):
        if not settings.database_url_file:
            raise ValueError('Protected database URL file required.')
        database = Database(settings.database_url_file.read_text().strip())
        try:
            if args.operation == 'restore':
                from clydex_cloud.storage.files import FileStorage
                from clydex_cloud.storage.recovery import restore_recovery
                if not args.file:
                    raise ValueError('--file required.')
                restore_recovery(database, FileStorage(settings.data_root / 'vault', settings.max_file_bytes),
                    settings.secrets_root, args.file, getpass.getpass('Owner recovery passphrase: '))
            elif args.operation == 'migrate':
                migrate(database)
            else:
                rollback_empty(database)
        finally:
            database.close()
        return
    runtime = Runtime(settings)
    try:
        if args.operation == 'provision':
            result = runtime.authentication.provision(input('Account login: '), getpass.getpass('New password: '))
            print('Store the one-time recovery code offline:', result['recovery_code'])
        elif args.operation == 'backup':
            from clydex_cloud.storage.recovery import export_recovery
            if not args.file:
                raise ValueError('--file required.')
            result = export_recovery(runtime.database, runtime.storage, runtime.cipher, args.file, getpass.getpass('Owner recovery passphrase: '))
            from sqlalchemy import select, insert
            from clydex_cloud.repositories.schema import accounts, backups
            import time
            import uuid
            with runtime.database.transaction() as c:
                for owner in c.execute(select(accounts.c.id)).scalars():
                    key = str(uuid.uuid4())
                    c.execute(insert(backups).values(id=key, owner_id=owner, sha256=result['sha256'],
                        size_bytes=result['size_bytes'], created_at=int(time.time()), status='exported'))
                    runtime.authentication.record(c, owner, 'backup.created', key)
        else:
            runtime.worker.start(1)
            try:
                runtime.worker.wait_closed()
            except KeyboardInterrupt:
                runtime.worker.close()
    finally:
        runtime.close()


if __name__ == '__main__':
    main()
