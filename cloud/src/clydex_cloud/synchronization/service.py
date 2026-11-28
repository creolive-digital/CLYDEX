from __future__ import annotations

import hashlib
import time
import uuid
from sqlalchemy import select, insert, update, delete

from clydex.synchronization.contracts import CATEGORIES, validate_payload
from clydex_cloud.core.encryption import encode
from clydex_cloud.core.errors import CloudError
from clydex.core.errors import PermissionDenied
from clydex_cloud.repositories.schema import (entities, changes, operations, preferences, memory_revisions,
    conversations, messages, devices, sync_state)


class Synchronization:
    def __init__(self, database, cipher, authentication, clock=time.time):
        self.db, self.cipher, self.auth, self.clock = database, cipher, authentication, clock
        self.knowledge_update = None

    def preference(self, connection, owner: str) -> dict:
        row = connection.execute(select(preferences).where(preferences.c.owner_id == owner,
            preferences.c.category == 'sync_policy')).mappings().first()
        return self.cipher.open(connection, owner, 'sync-policy', row['payload']) if row else {c: False for c in CATEGORIES}

    def configure(self, actor, value: dict) -> dict:
        actor.require('account.manage')
        if set(value) != set(CATEGORIES) or any(type(v) is not bool for v in value.values()):
            raise CloudError('invalid_sync_policy', 422)
        with self.db.transaction() as c:
            row = c.execute(select(preferences).where(preferences.c.owner_id == actor.owner_id,
                preferences.c.category == 'sync_policy')).mappings().first()
            values = dict(payload=self.cipher.seal(c, actor.owner_id, 'sync-policy', value),
                          revision=row['revision'] + 1 if row else 1)
            if row:
                c.execute(update(preferences).where(preferences.c.owner_id == actor.owner_id,
                    preferences.c.category == 'sync_policy').values(**values))
            else:
                c.execute(insert(preferences).values(owner_id=actor.owner_id, category='sync_policy', **values))
        return value

    def publish(self, connection, owner: str, category: str, key: str, payload: dict, *, deleted=False,
                base_version: int | None = None) -> dict:
        row = connection.execute(select(entities).where(entities.c.owner_id == owner,
            entities.c.category == category, entities.c.entity_id == key)).mappings().first()
        version = row['version'] if row else 0
        if base_version is not None and version != base_version:
            raise CloudError('sync_conflict', 409, current_version=version)
        next_version = version + 1
        if deleted:
            # Preserve revision/cursor tombstones without retaining deleted private
            # payloads in historical change feeds or memory revision rows.
            connection.execute(update(changes).where(changes.c.owner_id == owner, changes.c.category == category,
                changes.c.entity_id == key).values(payload=None, deleted=True))
            if category == 'memory':
                connection.execute(update(memory_revisions).where(memory_revisions.c.owner_id == owner,
                    memory_revisions.c.entity_id == key).values(payload=None, deleted=True))
        encrypted = None if deleted else self.cipher.seal(connection, owner, f'entity:{category}:{key}:{next_version}', payload)
        values = dict(version=next_version, payload=encrypted, deleted=deleted, updated_at=int(self.clock()))
        if row:
            result = connection.execute(update(entities).where(entities.c.owner_id == owner,
                entities.c.category == category, entities.c.entity_id == key, entities.c.version == version).values(**values))
            if result.rowcount != 1:
                raise CloudError('sync_conflict', 409, current_version=version)
        else:
            connection.execute(insert(entities).values(owner_id=owner, category=category, entity_id=key, **values))
        connection.execute(insert(changes).values(owner_id=owner, category=category, entity_id=key,
            version=next_version, payload=encrypted, deleted=deleted, created_at=int(self.clock())))
        return dict(category=category, entity_id=key, version=next_version, deleted=deleted)

    def push(self, actor, batch: list[dict]) -> dict:
        actor.require('sync.write')
        if not 1 <= len(batch) <= 20 or len(encode(batch)) > 256 * 1024:
            raise CloudError('sync_batch_limit', 413)
        results = []
        with self.db.transaction() as c:
            policy = self.preference(c, actor.owner_id)
            for operation in batch:
                category, key, op = operation['category'], operation['entity_id'], operation['operation_id']
                if not policy.get(category, False):
                    raise CloudError('sync_category_disabled', 403)
                try:
                    value = validate_payload(category, operation['payload'], deleted=operation['deleted'])
                except (ValueError, TypeError, PermissionDenied):
                    raise CloudError('unsafe_sync_payload', 422) from None
                digest = hashlib.sha256(encode(operation)).hexdigest()
                prior = c.execute(select(operations).where(operations.c.owner_id == actor.owner_id,
                    operations.c.operation_id == op)).mappings().first()
                if prior:
                    if prior['digest'] != digest:
                        raise CloudError('idempotency_mismatch', 409)
                    results.append(self.cipher.open(c, actor.owner_id, 'operation:' + op, prior['result']))
                    continue
                if category == 'knowledge':
                    actor.require('vault.write')
                    if self.knowledge_update is None:
                        raise CloudError('knowledge_metadata_unavailable', 409)
                    self.knowledge_update(c, actor.owner_id, key, value, operation['deleted'])
                elif category == 'devices':
                    actor.require('devices.manage')
                    if operation['deleted']:
                        raise CloudError('use_device_revocation_endpoint', 422)
                    result = c.execute(update(devices).where(devices.c.owner_id == actor.owner_id,
                        devices.c.id == key, devices.c.revoked_at.is_(None)).values(
                            profile=self.cipher.seal(c, actor.owner_id, 'device:' + key, value)))
                    if result.rowcount != 1:
                        raise CloudError('device_unavailable', 404)
                result = self.publish(c, actor.owner_id, category, key, value,
                    deleted=operation['deleted'], base_version=operation['base_version'])
                if category == 'memory':
                    c.execute(insert(memory_revisions).values(id=str(uuid.uuid4()), owner_id=actor.owner_id,
                        entity_id=key, version=result['version'], payload=None if operation['deleted'] else
                        self.cipher.seal(c, actor.owner_id, f'memory:{key}:{result["version"]}', value),
                        deleted=operation['deleted'], created_at=int(self.clock())))
                elif category == 'history':
                    old = c.execute(select(conversations.c.id).where(conversations.c.owner_id == actor.owner_id,
                        conversations.c.id == key)).first()
                    c.execute(delete(messages).where(messages.c.owner_id == actor.owner_id, messages.c.conversation_id == key))
                    values = dict(profile=self.cipher.seal(c, actor.owner_id, 'conversation:' + key,
                        {'title': value.get('title', 'Deleted conversation')}), revision=result['version'],
                        deleted_at=int(self.clock()) if operation['deleted'] else None)
                    if old:
                        c.execute(update(conversations).where(conversations.c.owner_id == actor.owner_id,
                            conversations.c.id == key).values(**values))
                    else:
                        c.execute(insert(conversations).values(id=key, owner_id=actor.owner_id, **values))
                    for index, message in enumerate(value.get('messages', [])):
                        message_id = str(uuid.uuid4())
                        c.execute(insert(messages).values(id=message_id, owner_id=actor.owner_id,
                            conversation_id=key, ordinal=index,
                            payload=self.cipher.seal(c, actor.owner_id, 'message:' + message_id, message)))
                c.execute(insert(operations).values(owner_id=actor.owner_id, operation_id=op, digest=digest,
                    result=self.cipher.seal(c, actor.owner_id, 'operation:' + op, result), created_at=int(self.clock())))
                self.auth.record(c, actor.owner_id, 'sync.applied', key)
                results.append(result)
        return {'results': results}

    def pull(self, actor, cursor: int = 0, limit: int = 100) -> dict:
        actor.require('sync.read')
        if not 0 <= cursor <= 2**63 - 1 or not 1 <= limit <= 500:
            raise CloudError('invalid_sync_cursor', 422)
        with self.db.transaction() as c:
            policy = self.preference(c, actor.owner_id)
            rows = list(c.execute(select(changes).where(changes.c.owner_id == actor.owner_id,
                changes.c.sequence > cursor).order_by(changes.c.sequence).limit(limit + 1)).mappings())
            result, last = [], cursor
            for row in rows[:limit]:
                last = row['sequence']
                if not policy.get(row['category'], False):
                    continue
                payload = {} if row['deleted'] else self.cipher.open(c, actor.owner_id,
                    f'entity:{row["category"]}:{row["entity_id"]}:{row["version"]}', row['payload'])
                result.append(dict(sequence=row['sequence'], category=row['category'], entity_id=row['entity_id'],
                    version=row['version'], deleted=row['deleted'], payload=payload))
            if actor.device_id:
                for category in CATEGORIES:
                    old = c.execute(select(sync_state).where(sync_state.c.owner_id == actor.owner_id,
                        sync_state.c.device_id == actor.device_id, sync_state.c.category == category)).first()
                    values = dict(cursor=last, updated_at=int(self.clock()))
                    if old:
                        c.execute(update(sync_state).where(sync_state.c.owner_id == actor.owner_id,
                            sync_state.c.device_id == actor.device_id, sync_state.c.category == category).values(**values))
                    else:
                        c.execute(insert(sync_state).values(owner_id=actor.owner_id, device_id=actor.device_id,
                            category=category, **values))
            return dict(changes=result, cursor=last, has_more=len(rows) > limit)
