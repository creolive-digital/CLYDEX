"""Bounded encrypted logical recovery exports. Operator maintenance interface only.

Restore is into a fresh schema and empty vault, never over an existing account.
This is separate from SQL Server native .bak/restore acceptance.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from sqlalchemy import select, insert, update
from clydex_cloud.core.encryption import VaultCipher, encode, decrypt
from clydex_cloud.repositories import schema as s

LIMIT = 256 * 1024 * 1024
HEADER = b'CLXREC1'


def recovery_key(passphrase, salt):
    if not isinstance(passphrase, str) or not 16 <= len(passphrase) <= 1024:
        raise ValueError('Recovery passphrases require 16–1024 characters.')
    return Scrypt(salt=salt, length=32, n=32768, r=8, p=1).derive(passphrase.encode())


def serial_row(row):
    return {k: {'binary': base64.b64encode(v).decode()} if isinstance(v, (bytes, memoryview)) else v for k, v in row.items()}


def export_recovery(database, storage, cipher, destination: Path, passphrase: str):
    if destination.exists() or destination.is_symlink():
        raise ValueError('Recovery destination must be a new private file.')
    rows, objects, total = {}, [], 0
    with database.transaction() as c:
        for table in s.metadata.sorted_tables:
            values = c.execute(select(table).limit(100001)).mappings().all()
            if len(values) > 100000:
                raise ValueError('Recovery export exceeds bounded logical export capacity.')
            rows[table.name] = [serial_row(row) for row in values]
            total += len(encode(rows[table.name]))
            if total > LIMIT // 2:
                raise ValueError('Recovery export capacity exceeded.')
        sources = [(r['owner_id'], r['object_id']) for r in c.execute(select(s.versions)).mappings()]
        sources += [(r['owner_id'], r['object_id']) for r in c.execute(select(s.garbage)).mappings()]
        for owner, key in sorted(set(sources)):
            path = storage.path(owner, key)
            if path.stat().st_size > storage.limit + 64:
                raise ValueError('Recovery object exceeds its bound.')
            data = path.read_bytes()
            total += len(data) * 4 // 3 + 256
            if total > LIMIT - 4096:
                raise ValueError('Recovery export capacity exceeded.')
            # Authenticate objects before admitting them into a recovery export.
            decrypt(cipher.owner_key(c, owner), data, f'file:{owner}:{key}'.encode())
            objects.append(dict(owner=owner, id=key, sha256=hashlib.sha256(data).hexdigest(), data=base64.b64encode(data).decode()))
    payload = encode(dict(version=1, created_at=int(time.time()), tables=rows, objects=objects,
        master=base64.b64encode(cipher.master_key).decode(), auth=base64.b64encode(cipher.auth_key).decode()))
    if len(payload) > LIMIT:
        raise ValueError('Recovery export capacity exceeded.')
    salt, nonce = os.urandom(16), os.urandom(12)
    content = HEADER + salt + nonce + AESGCM(recovery_key(passphrase, salt)).encrypt(nonce, payload, HEADER + salt)
    try:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        # Only our newly created destination is eligible for cleanup.
        if 'descriptor' in locals():
            destination.unlink(missing_ok=True)
        raise
    return dict(sha256=hashlib.sha256(content).hexdigest(), size_bytes=len(content), format='CLXREC1')


def restore_recovery(database, storage, keys_root: Path, source: Path, passphrase: str):
    if source.is_symlink() or not 64 <= source.stat().st_size <= LIMIT + 128:
        raise ValueError('Recovery input exceeds its format bounds.')
    data = source.read_bytes()
    if data[:7] != HEADER:
        raise ValueError('Unsupported recovery format.')
    payload = json.loads(AESGCM(recovery_key(passphrase, data[7:23])).decrypt(data[23:35], data[35:], data[:23]))
    if (set(payload) != {'version', 'created_at', 'tables', 'objects', 'master', 'auth'} or payload['version'] != 1
            or set(payload['tables']) != set(s.metadata.tables) or len(payload['objects']) > 20000):
        raise ValueError('Recovery manifest is incompatible.')
    cipher = VaultCipher(base64.b64decode(payload['master'], validate=True), base64.b64decode(payload['auth'], validate=True))
    if keys_root.is_symlink() or (keys_root.exists() and any(keys_root.iterdir())) or any(storage.root.iterdir()):
        raise ValueError('Recovery requires empty, isolated key and vault directories.')
    made, key_files = [], []
    now = int(time.time())
    try:
        with database.transaction() as c:
            for table in s.metadata.sorted_tables:
                if table is not s.schema_versions and c.execute(select(table).limit(1)).first():
                    raise ValueError('Recovery requires an empty database.')
            c.execute(s.schema_versions.delete())
            for table in s.metadata.sorted_tables:
                values = payload['tables'][table.name]
                if not isinstance(values, list) or len(values) > 100000:
                    raise ValueError('Invalid recovery row bound.')
                for row in values:
                    if set(row) != set(table.c.keys()):
                        raise ValueError('Invalid recovery columns.')
                    for column in table.c:
                        value = row[column.name]
                        if isinstance(value, dict):
                            if set(value) != {'binary'}:
                                raise ValueError('Invalid recovery binary.')
                            row[column.name] = base64.b64decode(value['binary'], validate=True)
                    if table in (s.sessions, s.devices):
                        row['revoked_at'] = now
                    if table is s.pairings:
                        row['expires_at'] = 0
                    if table is s.jobs and row['status'] in ('queued', 'running'):
                        row.update(status='queued', attempts=0, lease_until=None)
                identity = table in (s.changes, s.audit)
                if values:
                    if identity and not database.simulated:
                        c.exec_driver_sql(f'SET IDENTITY_INSERT {table.name} ON')
                    try:
                        c.execute(insert(table), values)
                    finally:
                        if identity and not database.simulated:
                            c.exec_driver_sql(f'SET IDENTITY_INSERT {table.name} OFF')
            expected = {(r['owner_id'], r['object_id']): r for r in c.execute(select(s.versions)).mappings()}
            garbage = {(r['owner_id'], r['object_id']) for r in c.execute(select(s.garbage)).mappings()}
            seen = set()
            for item in payload['objects']:
                owner, key = item['owner'], item['id']
                if (owner, key) in seen or ((owner, key) not in expected and (owner, key) not in garbage):
                    raise ValueError('Invalid recovery object identity.')
                blob = base64.b64decode(item['data'], validate=True)
                if hashlib.sha256(blob).hexdigest() != item['sha256']:
                    raise ValueError('Recovery checksum mismatch.')
                clear = decrypt(cipher.owner_key(c, owner), blob, f'file:{owner}:{key}'.encode())
                record = expected.get((owner, key))
                if record and (hashlib.sha256(clear).hexdigest() != record['sha256'] or len(clear) != record['size_bytes']):
                    raise ValueError('Restored content does not match database metadata.')
                storage.write_encrypted(owner, key, blob)
                made.append((owner, key))
                seen.add((owner, key))
            if seen != set(expected) | garbage:
                raise ValueError('Recovery is missing required file objects.')
            keys_root.mkdir(parents=True, mode=0o700, exist_ok=True)
            for name, content in (('master.key', cipher.master_key), ('auth.key', cipher.auth_key)):
                path = keys_root / name
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                key_files.append(path)
                with os.fdopen(descriptor, 'wb') as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
            # No recovered reusable credentials are valid after recovery.
            c.execute(update(s.sessions).values(revoked_at=now))
        return cipher
    except BaseException:
        for owner, key in made:
            storage.delete(owner, key)
        for path in key_files:
            path.unlink(missing_ok=True)
        raise
