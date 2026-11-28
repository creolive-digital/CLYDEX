"""Transactional metadata and encrypted private filesystem document management."""
from __future__ import annotations

import hashlib
import time
import uuid
from sqlalchemy import select, insert, update, delete, func

from clydex.knowledge.ingestion import filename, suffix, TEXT_SUFFIXES
from clydex_cloud.core.encryption import encode
from clydex_cloud.core.errors import CloudError
from clydex_cloud.repositories.schema import (accounts, collections, documents, versions, jobs,
    passages, chunk_terms, embeddings, operations, garbage)

ACCEPTED = TEXT_SUFFIXES | frozenset(('.html', '.htm', '.pdf', '.docx', '.xlsx', '.pptx', '.png', '.jpg', '.jpeg', '.wav'))


class KnowledgeVault:
    def __init__(self, database, cipher, authentication, storage, synchronization, settings, clock=time.time):
        self.db, self.cipher, self.auth, self.storage = database, cipher, authentication, storage
        self.sync, self.settings, self.clock = synchronization, settings, clock
        synchronization.knowledge_update = self.sync_metadata

    @staticmethod
    def owned(connection, table, owner: str, key: str, *, live=False):
        query = select(table).where(table.c.owner_id == owner, table.c.id == key)
        if live and 'deleted_at' in table.c:
            query = query.where(table.c.deleted_at.is_(None))
        row = connection.execute(query).mappings().first()
        if not row:
            raise CloudError('object_unavailable', 404)
        return row

    def create_collection(self, actor, profile: dict) -> dict:
        actor.require('vault.write')
        key = str(uuid.uuid4())
        with self.db.transaction() as c:
            count = c.execute(select(func.count()).select_from(collections).where(collections.c.owner_id == actor.owner_id,
                collections.c.deleted_at.is_(None))).scalar()
            if count >= 100:
                raise CloudError('collection_limit', 409)
            c.execute(insert(collections).values(id=key, owner_id=actor.owner_id,
                profile=self.cipher.seal(c, actor.owner_id, 'collection:' + key, profile), revision=1, created_at=int(self.clock())))
            self.auth.record(c, actor.owner_id, 'collection.created', key)
        return dict(id=key, revision=1, **profile)

    def list_collections(self, actor) -> dict:
        actor.require('vault.read')
        with self.db.transaction() as c:
            rows = c.execute(select(collections).where(collections.c.owner_id == actor.owner_id,
                collections.c.deleted_at.is_(None)).order_by(collections.c.created_at).limit(100)).mappings()
            key = self.cipher.owner(c, actor.owner_id)
            return {'items': [dict(id=r['id'], revision=r['revision'], **key.open('collection:' + r['id'], r['profile'])) for r in rows]}

    def document_dto(self, c, owner: str, row) -> dict:
        profile = self.cipher.open(c, owner, 'document:' + row['id'], row['profile'])
        version = c.execute(select(versions).where(versions.c.owner_id == owner,
            versions.c.document_id == row['id'], versions.c.version == row['current_version'])).mappings().first()
        return dict(id=row['id'], collection_id=row['collection_id'], version=row['current_version'],
            revision=row['revision'], status=row['status'], created_at=row['created_at'], **profile,
            size_bytes=version['size_bytes'] if version else 0, sha256=version['sha256'] if version else None)

    def list_documents(self, actor, collection_id=None) -> dict:
        actor.require('vault.read')
        with self.db.transaction() as c:
            query = select(documents).where(documents.c.owner_id == actor.owner_id, documents.c.deleted_at.is_(None))
            if collection_id:
                self.owned(c, collections, actor.owner_id, collection_id, live=True)
                query = query.where(documents.c.collection_id == collection_id)
            rows = list(c.execute(query.order_by(documents.c.created_at.desc()).limit(501)).mappings())
            return dict(items=[self.document_dto(c, actor.owner_id, r) for r in rows[:500]], truncated=len(rows) > 500)

    def _operation(self, c, owner, operation_id, digest):
        prior = c.execute(select(operations).where(operations.c.owner_id == owner,
            operations.c.operation_id == operation_id)).mappings().first()
        if prior:
            if prior['digest'] != digest:
                raise CloudError('idempotency_mismatch', 409)
            return self.cipher.open(c, owner, 'operation:' + operation_id, prior['result'])
        return None

    def _save_operation(self, c, owner, operation_id, digest, result):
        c.execute(insert(operations).values(owner_id=owner, operation_id=operation_id, digest=digest,
            result=self.cipher.seal(c, owner, 'operation:' + operation_id, result), created_at=int(self.clock())))

    def _enqueue(self, c, owner, document_id, version):
        count = c.execute(select(func.count()).select_from(jobs).where(jobs.c.owner_id == owner,
            jobs.c.status.in_(('queued', 'running')))).scalar()
        if count >= 32:
            raise CloudError('job_queue_full', 429, retry_after=30)
        key = str(uuid.uuid4())
        c.execute(insert(jobs).values(id=key, owner_id=owner, document_id=document_id, version=version,
            status='queued', error_code='', attempts=0, created_at=int(self.clock())))
        return key

    def upload(self, actor, collection_id: str, name: str, content: bytes, operation_id: str,
               *, document_id: str | None = None, expected_revision: int | None = None, source='selected_file', title='') -> dict:
        actor.require('vault.write')
        try:
            filename(name)
        except ValueError:
            raise CloudError('invalid_filename', 422) from None
        if suffix(name) not in ACCEPTED:
            raise CloudError('unsupported_format', 415)
        if not 0 < len(content) <= self.settings.max_file_bytes:
            raise CloudError('file_size_limit', 413)
        # Signature validation is immediate; deeper parsing happens in a bounded child.
        kind = suffix(name)
        if ((kind == '.pdf' and not content.startswith(b'%PDF-'))
                or (kind in ('.docx', '.xlsx', '.pptx') and not content.startswith(b'PK\x03\x04'))
                or (kind == '.png' and not content.startswith(b'\x89PNG\r\n\x1a\n'))
                or (kind in ('.jpg', '.jpeg') and not content.startswith(b'\xff\xd8\xff'))
                or (kind == '.wav' and not (content.startswith(b'RIFF') and content[8:12] == b'WAVE'))):
            raise CloudError('file_signature_mismatch', 415)
        checksum = hashlib.sha256(content).hexdigest()
        digest = hashlib.sha256(encode(dict(collection=collection_id, name=name, sha256=checksum,
            document_id=document_id, expected_revision=expected_revision, source=source, title=title))).hexdigest()
        object_id, key, written = str(uuid.uuid4()), document_id or str(uuid.uuid4()), False
        try:
            with self.db.transaction() as c:
                old_operation = self._operation(c, actor.owner_id, operation_id, digest)
                if old_operation:
                    return old_operation
                self.owned(c, collections, actor.owner_id, collection_id, live=True)
                current = self.owned(c, documents, actor.owner_id, key, live=True) if document_id else None
                if current and (current['revision'] != expected_revision or current['collection_id'] != collection_id):
                    raise CloudError('document_conflict', 409, current_version=current['revision'])
                if not current:
                    count = c.execute(select(func.count()).select_from(documents).where(documents.c.owner_id == actor.owner_id,
                        documents.c.deleted_at.is_(None))).scalar()
                    if count >= 10000:
                        raise CloudError('document_count_limit', 409)
                    duplicate = c.execute(select(versions.c.document_id).join(documents,
                        versions.c.document_id == documents.c.id).where(versions.c.owner_id == actor.owner_id,
                        versions.c.sha256 == checksum, documents.c.collection_id == collection_id,
                        versions.c.version == documents.c.current_version,
                        documents.c.deleted_at.is_(None))).first()
                    if duplicate:
                        result = dict(document_id=duplicate[0], duplicate=True)
                        self._save_operation(c, actor.owner_id, operation_id, digest, result)
                        return result
                reserved = c.execute(update(accounts).where(accounts.c.id == actor.owner_id,
                    accounts.c.used_bytes + len(content) <= accounts.c.quota_bytes).values(
                        used_bytes=accounts.c.used_bytes + len(content)))
                if reserved.rowcount != 1:
                    raise CloudError('storage_quota_exceeded', 413)
                next_version = current['current_version'] + 1 if current else 1
                revision = current['revision'] + 1 if current else 1
                profile = dict(name=name, source=source, title=title or name)
                values = dict(collection_id=collection_id,
                    profile=self.cipher.seal(c, actor.owner_id, 'document:' + key, profile),
                    current_version=next_version, revision=revision, status='queued')
                if current:
                    c.execute(update(documents).where(documents.c.id == key, documents.c.owner_id == actor.owner_id,
                        documents.c.revision == current['revision']).values(**values))
                    c.execute(update(jobs).where(jobs.c.owner_id == actor.owner_id, jobs.c.document_id == key,
                        jobs.c.status.in_(('queued', 'running'))).values(status='cancelled', lease_until=None))
                else:
                    c.execute(insert(documents).values(id=key, owner_id=actor.owner_id, created_at=int(self.clock()), **values))
                self.storage.write(actor.owner_id, object_id, content, self.cipher.owner_key(c, actor.owner_id))
                written = True
                c.execute(insert(versions).values(id=str(uuid.uuid4()), owner_id=actor.owner_id,
                    document_id=key, version=next_version, object_id=object_id, sha256=checksum,
                    size_bytes=len(content), created_at=int(self.clock()), parser='pending',
                    extraction=self.cipher.seal(c, actor.owner_id, f'version:{key}:{next_version}', profile)))
                job_id = self._enqueue(c, actor.owner_id, key, next_version)
                self.sync.publish(c, actor.owner_id, 'knowledge', key,
                    dict(document_id=key, name=name, version=next_version, revision=revision, status='queued'))
                self.auth.record(c, actor.owner_id, 'document.uploaded', key)
                result = dict(document_id=key, version=next_version, revision=revision, job_id=job_id, duplicate=False)
                self._save_operation(c, actor.owner_id, operation_id, digest, result)
                return result
        except Exception:
            if written:
                self.storage.delete(actor.owner_id, object_id)
            raise

    def content(self, actor, document_id: str, requested_version: int | None = None) -> tuple[dict, bytes]:
        actor.require('vault.read')
        with self.db.transaction() as c:
            document = self.owned(c, documents, actor.owner_id, document_id, live=True)
            version = c.execute(select(versions).where(versions.c.owner_id == actor.owner_id,
                versions.c.document_id == document_id, versions.c.version == (requested_version or document['current_version']))).mappings().first()
            if not version:
                raise CloudError('object_unavailable', 404)
            profile = self.document_dto(c, actor.owner_id, document)
            profile.update(self.cipher.open(c, actor.owner_id, f'version:{document_id}:{version["version"]}', version['extraction']))
            profile.update(version=version['version'], sha256=version['sha256'], size_bytes=version['size_bytes'])
            content = self.storage.read(actor.owner_id, version['object_id'],
                self.cipher.owner_key(c, actor.owner_id), version['sha256'])
            return profile, content

    def list_versions(self, actor, document_id: str) -> dict:
        actor.require('vault.read')
        with self.db.transaction() as c:
            self.owned(c, documents, actor.owner_id, document_id, live=True)
            rows = c.execute(select(versions).where(versions.c.owner_id == actor.owner_id,
                versions.c.document_id == document_id).order_by(versions.c.version.desc()).limit(100)).mappings()
            return {'items': [dict(version=r['version'], sha256=r['sha256'], size_bytes=r['size_bytes'],
                                   created_at=r['created_at'], parser=r['parser']) for r in rows]}

    def _clear_index(self, c, owner: str, document_id: str) -> None:
        ids = select(passages.c.id).where(passages.c.owner_id == owner, passages.c.document_id == document_id)
        c.execute(delete(chunk_terms).where(chunk_terms.c.owner_id == owner, chunk_terms.c.chunk_id.in_(ids)))
        c.execute(delete(embeddings).where(embeddings.c.owner_id == owner, embeddings.c.chunk_id.in_(ids)))
        c.execute(delete(passages).where(passages.c.owner_id == owner, passages.c.document_id == document_id))

    def _delete(self, c, owner: str, document):
        key = document['id']
        if document['deleted_at'] is not None:
            return
        self._clear_index(c, owner, key)
        c.execute(update(jobs).where(jobs.c.owner_id == owner, jobs.c.document_id == key).values(status='cancelled', lease_until=None))
        rows = c.execute(select(versions).where(versions.c.owner_id == owner, versions.c.document_id == key)).mappings()
        for row in rows:
            c.execute(insert(garbage).values(owner_id=owner, object_id=row['object_id'],
                size_bytes=row['size_bytes'], created_at=int(self.clock())))
        c.execute(delete(versions).where(versions.c.owner_id == owner, versions.c.document_id == key))
        c.execute(update(documents).where(documents.c.owner_id == owner, documents.c.id == key).values(
            deleted_at=int(self.clock()), status='deleted', revision=document['revision'] + 1,
            profile=self.cipher.seal(c, owner, 'document:' + key, {'name': 'Deleted document', 'source': 'deleted'})))
        self.auth.record(c, owner, 'document.deleted', key)

    def delete_document(self, actor, key: str, expected_revision: int) -> dict:
        actor.require('vault.write')
        with self.db.transaction() as c:
            row = self.owned(c, documents, actor.owner_id, key)
            if row['deleted_at'] is None and row['revision'] != expected_revision:
                raise CloudError('document_conflict', 409, current_version=row['revision'])
            if row['deleted_at'] is None:
                self._delete(c, actor.owner_id, row)
                self.sync.publish(c, actor.owner_id, 'knowledge', key, {}, deleted=True)
        self.collect_garbage()
        return {'deleted': True}

    def delete_collection(self, actor, key: str, expected_revision: int) -> dict:
        actor.require('vault.write')
        with self.db.transaction() as c:
            row = self.owned(c, collections, actor.owner_id, key)
            if row['deleted_at'] is not None:
                return {'deleted': True}
            if row['revision'] != expected_revision:
                raise CloudError('collection_conflict', 409, current_version=row['revision'])
            count = c.execute(select(func.count()).select_from(documents).where(documents.c.owner_id == actor.owner_id,
                documents.c.collection_id == key, documents.c.deleted_at.is_(None))).scalar()
            if count:
                raise CloudError('collection_not_empty', 409)
            c.execute(update(collections).where(collections.c.owner_id == actor.owner_id, collections.c.id == key).values(
                deleted_at=int(self.clock()), revision=row['revision'] + 1,
                profile=self.cipher.seal(c, actor.owner_id, 'collection:' + key, {'title': 'Deleted collection', 'description': ''})))
            self.auth.record(c, actor.owner_id, 'collection.deleted', key)
        return {'deleted': True}

    def reprocess(self, actor, key: str, expected_revision: int) -> dict:
        actor.require('vault.write')
        with self.db.transaction() as c:
            row = self.owned(c, documents, actor.owner_id, key, live=True)
            if row['revision'] != expected_revision:
                raise CloudError('document_conflict', 409, current_version=row['revision'])
            c.execute(update(jobs).where(jobs.c.owner_id == actor.owner_id, jobs.c.document_id == key,
                jobs.c.status.in_(('queued', 'running'))).values(status='cancelled', lease_until=None))
            job = self._enqueue(c, actor.owner_id, key, row['current_version'])
            c.execute(update(documents).where(documents.c.owner_id == actor.owner_id, documents.c.id == key).values(
                status='queued', revision=row['revision'] + 1))
            self._clear_index(c, actor.owner_id, key)
        return {'job_id': job, 'status': 'queued'}

    def sync_metadata(self, c, owner: str, key: str, payload: dict, deleted: bool) -> None:
        row = self.owned(c, documents, owner, key, live=True)
        if deleted:
            self._delete(c, owner, row)
        else:
            profile = self.cipher.open(c, owner, 'document:' + key, row['profile'])
            profile['title'] = payload['title']
            c.execute(update(documents).where(documents.c.owner_id == owner, documents.c.id == key).values(
                profile=self.cipher.seal(c, owner, 'document:' + key, profile), revision=row['revision'] + 1))

    def collect_garbage(self) -> int:
        completed = 0
        with self.db.transaction() as c:
            for row in list(c.execute(select(garbage).limit(32)).mappings()):
                try:
                    self.storage.delete(row['owner_id'], row['object_id'])
                except OSError:
                    continue
                c.execute(delete(garbage).where(garbage.c.owner_id == row['owner_id'], garbage.c.object_id == row['object_id']))
                c.execute(update(accounts).where(accounts.c.id == row['owner_id']).values(
                    used_bytes=accounts.c.used_bytes - row['size_bytes']))
                completed += 1
        return completed

    def usage(self, actor) -> dict:
        with self.db.transaction() as c:
            row = c.execute(select(accounts.c.used_bytes, accounts.c.quota_bytes).where(accounts.c.id == actor.owner_id)).one()
            pending = c.execute(select(func.coalesce(func.sum(garbage.c.size_bytes), 0)).where(garbage.c.owner_id == actor.owner_id)).scalar()
            return dict(document_bytes=row[0], quota_bytes=row[1], pending_delete_bytes=pending)
