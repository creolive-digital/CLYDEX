from __future__ import annotations

import json
import secrets
import time
import uuid
from sqlalchemy import select, insert, update, func

from clydex_cloud.authentication.service import DEVICE_SCOPES
from clydex_cloud.core.errors import CloudError
from clydex_cloud.repositories.schema import devices, pairings, sessions, accounts


class DeviceService:
    def __init__(self, database, cipher, authentication, clock=time.time):
        self.database, self.cipher, self.auth, self.clock = database, cipher, authentication, clock

    def list(self, actor) -> list[dict]:
        with self.database.transaction() as connection:
            rows = connection.execute(select(devices).where(devices.c.owner_id == actor.owner_id)
                .order_by(devices.c.created_at).limit(100)).mappings()
            return [dict(id=r['id'], **self.cipher.open(connection, actor.owner_id, 'device:' + r['id'], r['profile']),
                scopes=json.loads(r['scopes']), last_seen=r['last_seen'], revoked=r['revoked_at'] is not None,
                revoked_at=r['revoked_at'],
                credential_version=r['credential_version']) for r in rows]

    def request_pairing(self, actor, profile: dict, scopes: list[str]) -> dict:
        actor.require('devices.manage')
        if not scopes or not set(scopes) <= DEVICE_SCOPES:
            raise CloudError('invalid_device_scopes', 422)
        key, token, now = str(uuid.uuid4()), secrets.token_urlsafe(48), int(self.clock())
        with self.database.transaction() as connection:
            count = connection.execute(select(func.count()).select_from(pairings).where(pairings.c.owner_id == actor.owner_id,
                pairings.c.expires_at > now, pairings.c.claimed_at.is_(None))).scalar()
            if count >= 16:
                raise CloudError('pairing_limit', 429, retry_after=180)
            connection.execute(insert(pairings).values(id=key, owner_id=actor.owner_id,
                profile=self.cipher.seal(connection, actor.owner_id, 'pairing:' + key, profile),
                scopes=json.dumps(sorted(set(scopes))), claim_hash=self.cipher.digest('pairing', token), expires_at=now + 180))
        # The pending token cannot be claimed before independent owner approval.
        return dict(id=key, pairing_token=token, expires_in=180, approved=False)

    def approve(self, actor, key: str) -> dict:
        actor.require('devices.manage')
        with self.database.transaction() as connection:
            row = connection.execute(select(pairings).where(pairings.c.owner_id == actor.owner_id,
                pairings.c.id == key)).mappings().first()
            if not row or row['expires_at'] <= self.clock() or row['claimed_at'] is not None:
                raise CloudError('pairing_unavailable', 404)
            connection.execute(update(pairings).where(pairings.c.owner_id == actor.owner_id,
                pairings.c.id == key).values(approved_at=int(self.clock())))
        return {'approved': True}

    def claim(self, token: str) -> dict:
        now, key = int(self.clock()), str(uuid.uuid4())
        with self.database.transaction() as connection:
            row = connection.execute(select(pairings).where(pairings.c.claim_hash == self.cipher.digest('pairing', token))).mappings().first()
            if not row or row['approved_at'] is None or row['claimed_at'] is not None or row['expires_at'] <= now:
                raise CloudError('pairing_unavailable', 401)
            disabled = connection.execute(select(accounts.c.disabled).where(accounts.c.id == row['owner_id'])).scalar()
            if disabled is not False:
                raise CloudError('pairing_unavailable', 401)
            count = connection.execute(select(func.count()).select_from(devices).where(devices.c.owner_id == row['owner_id'])).scalar()
            if count >= 100:
                raise CloudError('device_limit', 409)
            changed = connection.execute(update(pairings).where(pairings.c.id == row['id'],
                pairings.c.claimed_at.is_(None), pairings.c.expires_at > now).values(claimed_at=now))
            if changed.rowcount != 1:
                raise CloudError('pairing_unavailable', 401)
            profile = self.cipher.open(connection, row['owner_id'], 'pairing:' + row['id'], row['profile'])
            scopes = json.loads(row['scopes'])
            connection.execute(insert(devices).values(id=key, owner_id=row['owner_id'],
                profile=self.cipher.seal(connection, row['owner_id'], 'device:' + key, profile),
                scopes=row['scopes'], created_at=now, last_seen=now, credential_version=1))
            self.auth.record(connection, row['owner_id'], 'device.paired', key)
            return self.auth.issue(connection, row['owner_id'], scopes=scopes, device_id=key)

    def revoke(self, actor, key: str) -> dict:
        actor.require('devices.manage')
        with self.database.transaction() as connection:
            result = connection.execute(update(devices).where(devices.c.owner_id == actor.owner_id,
                devices.c.id == key).values(revoked_at=int(self.clock())))
            if not result.rowcount:
                raise CloudError('device_unavailable', 404)
            connection.execute(update(sessions).where(sessions.c.owner_id == actor.owner_id,
                sessions.c.device_id == key).values(revoked_at=int(self.clock())))
            self.auth.record(connection, actor.owner_id, 'device.revoked', key)
        return {'revoked': True}

    def rotate(self, actor, key: str) -> dict:
        actor.require('devices.manage')
        with self.database.transaction() as connection:
            row = connection.execute(select(devices).where(devices.c.owner_id == actor.owner_id,
                devices.c.id == key, devices.c.revoked_at.is_(None))).mappings().first()
            if not row:
                raise CloudError('device_unavailable', 404)
            connection.execute(update(sessions).where(sessions.c.owner_id == actor.owner_id,
                sessions.c.device_id == key).values(revoked_at=int(self.clock())))
            connection.execute(update(devices).where(devices.c.owner_id == actor.owner_id,
                devices.c.id == key).values(credential_version=row['credential_version'] + 1))
            self.auth.record(connection, actor.owner_id, 'device.rotated', key)
            return self.auth.issue(connection, actor.owner_id, scopes=json.loads(row['scopes']), device_id=key)
