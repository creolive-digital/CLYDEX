"""Argon2id passwords; opaque, short-lived access and single-use rotating refresh.

Every authenticated request checks account/session/device revocation in SQL.
Bearer tokens are never authentication shortcuts around ownership or scopes.
"""
from dataclasses import dataclass
import hmac
import json
import secrets
import time
import unicodedata
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import select, insert, update, func
from sqlalchemy.exc import IntegrityError

from clydex_cloud.core.errors import CloudError
from clydex_cloud.repositories.schema import accounts, devices, sessions, refresh_uses, audit, invitation_uses

ACCOUNT_SCOPES = frozenset(('account.manage', 'devices.manage', 'vault.read', 'vault.write', 'sync.read', 'sync.write'))
DEVICE_SCOPES = frozenset(('vault.read', 'vault.write', 'sync.read', 'sync.write'))


def identity(value: str) -> str:
    value = unicodedata.normalize('NFKC', value).strip().casefold()
    if not 3 <= len(value) <= 160 or any(unicodedata.category(c)[0] == 'C' for c in value):
        raise CloudError('invalid_login', 422)
    return value


@dataclass(frozen=True)
class Principal:
    owner_id: str
    session_id: str
    device_id: str | None
    scopes: frozenset[str]

    def require(self, scope: str) -> None:
        if scope not in self.scopes:
            raise CloudError('scope_denied', 403)


class Authentication:
    def __init__(self, database, cipher, settings, clock=time.time):
        self.database, self.cipher, self.settings, self.clock = database, cipher, settings, clock
        self.passwords = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
        self._dummy = self.passwords.hash(secrets.token_urlsafe(32))

    def provision(self, login: str, password: str, *, invitation_digest=None) -> dict:
        if not 12 <= len(password) <= 256:
            raise CloudError('invalid_password', 422)
        owner, recovery = str(uuid.uuid4()), secrets.token_urlsafe(48)
        login = identity(login)
        try:
            with self.database.transaction() as connection:
                if invitation_digest:
                    connection.execute(insert(invitation_uses).values(digest=invitation_digest, used_at=int(self.clock())))
                connection.execute(insert(accounts).values(id=owner, login_hash=self.cipher.digest('login', login),
                    profile=b'pending', password_hash=self.passwords.hash(password),
                    recovery_hash=self.cipher.digest('recovery', recovery), created_at=int(self.clock()), disabled=False,
                    used_bytes=0, quota_bytes=self.settings.quota_bytes))
                self.cipher.new_owner(connection, owner)
                connection.execute(update(accounts).where(accounts.c.id == owner).values(
                    profile=self.cipher.seal(connection, owner, 'account', dict(login=login))))
                self.record(connection, owner, 'account.provisioned')
        except IntegrityError:
            raise CloudError('account_unavailable', 409) from None
        return dict(account_id=owner, recovery_code=recovery)

    def record(self, connection, owner: str, code: str, object_id=None) -> None:
        allowed = {'account.provisioned', 'account.login', 'account.recovered', 'session.logout', 'session.replay',
                   'device.paired', 'device.revoked', 'device.rotated', 'document.uploaded', 'document.deleted',
                   'sync.applied', 'collection.created', 'collection.deleted', 'backup.created'}
        if code not in allowed:
            raise ValueError('Unknown audit code.')
        connection.execute(insert(audit).values(owner_id=owner, code=code, object_id=object_id, created_at=int(self.clock())))

    def issue(self, connection, owner: str, scopes=ACCOUNT_SCOPES, device_id=None) -> dict:
        now, key = int(self.clock()), str(uuid.uuid4())
        count = connection.execute(select(func.count()).select_from(sessions).where(sessions.c.owner_id == owner,
            sessions.c.revoked_at.is_(None), sessions.c.refresh_expires > now)).scalar()
        if count >= 32:
            raise CloudError('session_limit', 429, retry_after=60)
        access, refresh = 'clxa.' + key + '.' + secrets.token_urlsafe(32), 'clxr.' + key + '.' + secrets.token_urlsafe(48)
        connection.execute(insert(sessions).values(id=key, owner_id=owner, device_id=device_id,
            access_hash=self.cipher.digest('access', access), refresh_hash=self.cipher.digest('refresh', refresh),
            scopes=json.dumps(sorted(scopes)), created_at=now, access_expires=now + self.settings.access_seconds,
            refresh_expires=now + self.settings.refresh_seconds, generation=1))
        return dict(access_token=access, refresh_token=refresh, expires_in=self.settings.access_seconds,
                    account_id=owner, device_id=device_id, scopes=sorted(scopes))

    def login(self, login: str, password: str) -> dict:
        lookup = self.cipher.digest('login', identity(login))
        with self.database.transaction() as connection:
            row = connection.execute(select(accounts).where(accounts.c.login_hash == lookup)).mappings().first()
            try:
                self.passwords.verify(row['password_hash'] if row else self._dummy, password)
            except VerificationError:
                raise CloudError('authentication_failed', 401) from None
            if not row or row['disabled']:
                raise CloudError('authentication_failed', 401)
            if self.passwords.check_needs_rehash(row['password_hash']):
                connection.execute(update(accounts).where(accounts.c.id == row['id']).values(password_hash=self.passwords.hash(password)))
            self.record(connection, row['id'], 'account.login')
            return self.issue(connection, row['id'])

    @staticmethod
    def token_id(token: str, prefix: str) -> str:
        try:
            pieces = token.split('.')
            if len(token) > 256 or len(pieces) != 3 or pieces[0] != prefix or len(pieces[2]) < 40:
                raise ValueError
            return str(uuid.UUID(pieces[1]))
        except (ValueError, AttributeError):
            raise CloudError('authentication_failed', 401) from None

    def active(self, connection, row) -> None:
        if row is None or row['revoked_at'] is not None:
            raise CloudError('authentication_failed', 401)
        account = connection.execute(select(accounts.c.disabled).where(accounts.c.id == row['owner_id'])).first()
        if not account or account[0]:
            raise CloudError('authentication_failed', 401)
        if row['device_id']:
            device = connection.execute(select(devices).where(devices.c.id == row['device_id'],
                devices.c.owner_id == row['owner_id'])).mappings().first()
            if not device or device['revoked_at'] is not None:
                raise CloudError('device_revoked', 401)

    def authenticate(self, token: str) -> Principal:
        key = self.token_id(token, 'clxa')
        with self.database.transaction() as connection:
            row = connection.execute(select(sessions).where(sessions.c.id == key)).mappings().first()
            self.active(connection, row)
            if int(self.clock()) >= row['access_expires'] or not hmac.compare_digest(
                    row['access_hash'], self.cipher.digest('access', token)):
                raise CloudError('authentication_failed', 401)
            if row['device_id']:
                connection.execute(update(devices).where(devices.c.id == row['device_id'],
                    devices.c.owner_id == row['owner_id'], devices.c.last_seen < int(self.clock()) - 60).values(last_seen=int(self.clock())))
            return Principal(row['owner_id'], key, row['device_id'], frozenset(json.loads(row['scopes'])))

    def rotate(self, token: str) -> dict:
        key, digest, now = self.token_id(token, 'clxr'), self.cipher.digest('refresh', token), int(self.clock())
        replay = False
        with self.database.transaction() as connection:
            row = connection.execute(select(sessions).where(sessions.c.id == key)).mappings().first()
            self.active(connection, row)
            used = connection.execute(select(refresh_uses.c.token_hash).where(refresh_uses.c.token_hash == digest)).first()
            if used:
                connection.execute(update(sessions).where(sessions.c.id == key).values(revoked_at=now))
                self.record(connection, row['owner_id'], 'session.replay', key)
                replay = True
            elif row['refresh_expires'] <= now or not hmac.compare_digest(row['refresh_hash'], digest):
                raise CloudError('authentication_failed', 401)
            else:
                access = 'clxa.' + key + '.' + secrets.token_urlsafe(32)
                refresh = 'clxr.' + key + '.' + secrets.token_urlsafe(48)
                connection.execute(insert(refresh_uses).values(token_hash=digest, session_id=key,
                    used_at=now, expires_at=row['refresh_expires']))
                changed = connection.execute(update(sessions).where(sessions.c.id == key,
                    sessions.c.generation == row['generation'], sessions.c.refresh_hash == digest,
                    sessions.c.revoked_at.is_(None)).values(generation=row['generation'] + 1,
                    access_hash=self.cipher.digest('access', access), refresh_hash=self.cipher.digest('refresh', refresh),
                    access_expires=now + self.settings.access_seconds))
                if changed.rowcount != 1:
                    raise CloudError('refresh_conflict', 409)
                result = dict(access_token=access, refresh_token=refresh, expires_in=self.settings.access_seconds,
                    account_id=row['owner_id'], device_id=row['device_id'], scopes=json.loads(row['scopes']))
        if replay:
            raise CloudError('refresh_reuse_revoked', 401)
        return result

    def logout(self, actor: Principal, all_sessions=False) -> dict:
        with self.database.transaction() as connection:
            query = update(sessions).where(sessions.c.owner_id == actor.owner_id)
            if not all_sessions:
                query = query.where(sessions.c.id == actor.session_id)
            else:
                actor.require('account.manage')
            connection.execute(query.values(revoked_at=int(self.clock())))
            self.record(connection, actor.owner_id, 'session.logout', actor.session_id)
        return {'revoked': True}

    def recover(self, login: str, code: str, password: str) -> dict:
        if not 12 <= len(password) <= 256:
            raise CloudError('invalid_password', 422)
        next_code = secrets.token_urlsafe(48)
        with self.database.transaction() as connection:
            row = connection.execute(select(accounts).where(accounts.c.login_hash == self.cipher.digest('login', identity(login)))).mappings().first()
            if not row or row['disabled'] or not hmac.compare_digest(row['recovery_hash'], self.cipher.digest('recovery', code)):
                raise CloudError('authentication_failed', 401)
            connection.execute(update(accounts).where(accounts.c.id == row['id']).values(
                password_hash=self.passwords.hash(password), recovery_hash=self.cipher.digest('recovery', next_code)))
            connection.execute(update(sessions).where(sessions.c.owner_id == row['id']).values(revoked_at=int(self.clock())))
            self.record(connection, row['id'], 'account.recovered')
        return dict(recovered=True, recovery_code=next_code)
