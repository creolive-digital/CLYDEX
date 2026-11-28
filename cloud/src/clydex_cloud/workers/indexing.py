"""SQL-leased bounded workers. No task outlives owned shutdown or publishes stale indices."""
from __future__ import annotations

import threading
import time
import uuid
from sqlalchemy import select, update, insert, delete, or_, func

from clydex.knowledge.models import terms
from clydex_cloud.core.errors import CloudError
from clydex_cloud.repositories.schema import jobs, documents, versions, passages, chunk_terms, embeddings, audit, refresh_uses
from clydex_cloud.workers.parsing import parse_owned


class IndexWorker:
    def __init__(self, database, cipher, vault, embedding_service, *, parser=parse_owned, clock=time.time):
        self.db, self.cipher, self.vault, self.embeddings = database, cipher, vault, embedding_service
        self.parser, self.clock = parser, clock
        self.stopped, self.threads = threading.Event(), []
        self._retention_at = 0

    def start(self, concurrency=1):
        if not 1 <= concurrency <= 4 or self.threads:
            raise ValueError('Invalid worker concurrency or duplicate start.')
        for index in range(concurrency):
            thread = threading.Thread(target=self._run, name=f'clydex-vault-worker-{index}', daemon=False)
            self.threads.append(thread)
            thread.start()

    def _run(self):
        while not self.stopped.is_set():
            try:
                if not self.tick():
                    self.stopped.wait(.5)
            except Exception:
                # Only generic status reaches the configured API logger; no job body/trace.
                self.stopped.wait(1)

    def _claim(self):
        now = int(self.clock())
        with self.db.transaction() as c:
            c.execute(update(jobs).where(jobs.c.status == 'running', jobs.c.lease_until < now,
                jobs.c.attempts >= 3).values(status='failed', error_code='lease_exhausted', lease_until=None))
            row = c.execute(select(jobs).where(jobs.c.attempts < 3,
                or_(jobs.c.status == 'queued', (jobs.c.status == 'running') & (jobs.c.lease_until < now)))
                .order_by(jobs.c.created_at).limit(1)).mappings().first()
            if not row:
                return None
            changed = c.execute(update(jobs).where(jobs.c.id == row['id'], jobs.c.attempts == row['attempts'],
                or_(jobs.c.status == 'queued', (jobs.c.status == 'running') & (jobs.c.lease_until < now))).values(
                    status='running', attempts=row['attempts'] + 1, lease_until=now + 120))
            if changed.rowcount != 1:
                return None
            return dict(row, attempts=row['attempts'] + 1)

    def _live(self, c, job):
        current = c.execute(select(jobs).where(jobs.c.id == job['id'], jobs.c.owner_id == job['owner_id'],
            jobs.c.status == 'running', jobs.c.attempts == job['attempts'],
            jobs.c.lease_until >= int(self.clock()))).mappings().first()
        document = c.execute(select(documents).where(documents.c.id == job['document_id'],
            documents.c.owner_id == job['owner_id'], documents.c.deleted_at.is_(None),
            documents.c.current_version == job['version'])).mappings().first()
        if not current or not document or self.stopped.is_set():
            raise CloudError('processing_interrupted', 409)
        return document

    def tick(self) -> bool:
        if self.clock() >= self._retention_at:
            with self.db.transaction() as c:
                c.execute(delete(refresh_uses).where(refresh_uses.c.expires_at < int(self.clock())))
                days = self.vault.settings.audit_retention_days
                if days:
                    c.execute(delete(audit).where(audit.c.created_at < int(self.clock()) - days * 86400))
            self._retention_at = self.clock() + 3600
        self.vault.collect_garbage()
        job = self._claim()
        if not job:
            return False
        owner, document_id = job['owner_id'], job['document_id']
        try:
            with self.db.transaction() as c:
                document = self._live(c, job)
                profile = self.cipher.open(c, owner, 'document:' + document_id, document['profile'])
                version = c.execute(select(versions).where(versions.c.owner_id == owner,
                    versions.c.document_id == document_id, versions.c.version == job['version'])).mappings().one()
                content = self.vault.storage.read(owner, version['object_id'], self.cipher.owner_key(c, owner), version['sha256'])
            result = self.parser(profile['name'], content, self.stopped)
            parsed = result.get('passages', [])
            if len(parsed) > 2000 or sum(len(p['text']) for p in parsed) > 2_000_000:
                raise CloudError('extracted_content_limit', 422)
            vectors, warning = [], result.get('warning', '')
            if self.embeddings.configured and result['status'] == 'ready':
                try:
                    for start in range(0, len(parsed), 32):
                        vectors.extend(self.embeddings.embed([p['text'] for p in parsed[start:start + 32]]))
                        with self.db.transaction() as c:
                            self._live(c, job)
                            c.execute(update(jobs).where(jobs.c.id == job['id'], jobs.c.owner_id == owner,
                                jobs.c.attempts == job['attempts']).values(lease_until=int(self.clock()) + 120))
                except Exception:
                    vectors, warning = [], 'embedding_unavailable'
            with self.db.transaction() as c:
                document = self._live(c, job)
                key = self.cipher.owner(c, owner)
                self.vault._clear_index(c, owner, document_id)
                count = c.execute(select(func.count()).select_from(passages).where(passages.c.owner_id == owner)).scalar()
                if count + len(parsed) > 10000:
                    raise CloudError('index_quota_exceeded', 422)
                for index, passage in enumerate(parsed):
                    chunk_id = str(uuid.uuid4())
                    if not 0 < len(passage['text']) <= 2000 or len(passage['location']) > 200:
                        raise CloudError('parser_protocol_failure', 422)
                    c.execute(insert(passages).values(id=chunk_id, owner_id=owner, document_id=document_id,
                        version=job['version'], ordinal=index, payload=key.seal('chunk:' + chunk_id, passage)))
                    tokens = set(terms(passage['text'])[:128])
                    if tokens:
                        c.execute(insert(chunk_terms), [dict(owner_id=owner, chunk_id=chunk_id, term_hash=key.term(t)) for t in tokens])
                    if vectors:
                        model = self.embeddings.settings
                        embedding_id = str(uuid.uuid4())
                        c.execute(insert(embeddings).values(id=embedding_id, owner_id=owner, chunk_id=chunk_id,
                            model=model.embedding_model, model_revision=model.embedding_revision,
                            dimensions=model.embedding_dimensions, payload=key.seal('embedding:' + embedding_id, vectors[index]),
                            created_at=int(self.clock())))
                c.execute(update(versions).where(versions.c.id == version['id'], versions.c.owner_id == owner).values(
                    parser=result['parser'], extraction=key.seal(f'version:{document_id}:{job["version"]}',
                        dict(profile, parser=result['parser'], warning=warning, chunk_count=len(parsed)))))
                c.execute(update(documents).where(documents.c.owner_id == owner, documents.c.id == document_id,
                    documents.c.current_version == job['version']).values(status=result['status'], revision=document['revision'] + 1))
                c.execute(update(jobs).where(jobs.c.id == job['id'], jobs.c.owner_id == owner,
                    jobs.c.attempts == job['attempts']).values(status='partial' if warning else 'succeeded',
                        error_code=warning, lease_until=None))
                self.vault.sync.publish(c, owner, 'knowledge', document_id,
                    dict(document_id=document_id, name=profile['name'], version=job['version'],
                         revision=document['revision'] + 1, status=result['status']))
            return True
        except Exception as exc:
            allowed = exc.code if isinstance(exc, CloudError) else 'processing_failed'
            with self.db.transaction() as c:
                changed = c.execute(update(jobs).where(jobs.c.id == job['id'], jobs.c.owner_id == owner,
                    jobs.c.status == 'running', jobs.c.attempts == job['attempts']).values(
                        status='queued' if self.stopped.is_set() and job['attempts'] < 3 else 'failed',
                        error_code=allowed[:80], lease_until=None))
                if changed.rowcount:
                    c.execute(update(documents).where(documents.c.id == document_id, documents.c.owner_id == owner,
                        documents.c.current_version == job['version'], documents.c.deleted_at.is_(None)).values(status='error'))
            return True

    def close(self) -> None:
        self.stopped.set()

    def wait_closed(self) -> None:
        for thread in self.threads:
            thread.join()
