"""Owned blind-keyword retrieval and gated SQL Server native exact distance.

Embeddings remain encrypted in SQL. A bounded owner/collection/model-filtered
candidate set is decrypted server-side and passed as parameters to native VECTOR
distance expressions. No ANN preview, separate vector DB or remote embeddings.
"""
import json
import math
from sqlalchemy import select

from clydex.knowledge.models import citation_id, terms
from clydex_cloud.core.errors import CloudError
from clydex_cloud.repositories.schema import documents, passages, chunk_terms, embeddings


class Retrieval:
    def __init__(self, database, cipher, embedding_service, *, native_distance=None):
        self.db, self.cipher, self.embeddings = database, cipher, embedding_service
        self._native = native_distance or self.native_distance

    def native_distance(self, connection, vector: list[float], candidates: list[tuple[str, list[float]]]) -> dict:
        if self.db.simulated:
            raise CloudError('native_vector_not_verified', 409)
        major = connection.exec_driver_sql("SELECT CAST(SERVERPROPERTY('ProductMajorVersion') AS INT)").scalar()
        if major != 17:
            raise CloudError('native_vector_version_unsupported', 409)
        dimension = len(vector)
        if not 1 <= dimension <= 1998 or len(candidates) > 1000:
            raise CloudError('native_vector_query_limit', 422)
        # The type dimension is a validated integer, not interpolated user SQL.
        result = {}
        # SQL Server permits at most 2100 parameters; batches stay below it.
        for start in range(0, len(candidates), 600):
            batch = candidates[start:start + 600]
            values = ','.join(f'(?, VECTOR_DISTANCE(\'cosine\', CAST(? AS VECTOR({dimension})), CAST(? AS VECTOR({dimension}))))'
                              for _ in batch)
            parameters = []
            for key, candidate in batch:
                parameters.extend((key, json.dumps(vector, allow_nan=False), json.dumps(candidate, allow_nan=False)))
            query = 'SELECT chunk_id, distance FROM (VALUES ' + values + ') AS d(chunk_id, distance)'
            result.update({row[0]: float(row[1]) for row in connection.exec_driver_sql(query, tuple(parameters))})
        return result

    def search(self, actor, query: str, collection_id=None, mode='keyword', limit=5) -> dict:
        actor.require('vault.read')
        if not 1 <= len(query.strip()) <= 1000 or not 1 <= limit <= 20 or mode not in ('keyword', 'semantic'):
            raise CloudError('invalid_search', 422)
        vector = self.embeddings.embed([query])[0] if mode == 'semantic' else None
        with self.db.transaction() as c:
            key = self.cipher.owner(c, actor.owner_id)
            base = select(passages, documents.c.profile.label('document_profile'), documents.c.revision,
                          documents.c.collection_id).join(documents, passages.c.document_id == documents.c.id).where(
                passages.c.owner_id == actor.owner_id, documents.c.owner_id == actor.owner_id,
                documents.c.deleted_at.is_(None), documents.c.status == 'ready',
                passages.c.version == documents.c.current_version)
            if collection_id:
                base = base.where(documents.c.collection_id == collection_id)
            tokens = list(dict.fromkeys(terms(query)))[:16]
            if not tokens:
                return dict(items=[], mode=mode, insufficient_evidence=True)
            if mode == 'keyword':
                matching = select(chunk_terms.c.chunk_id).where(chunk_terms.c.owner_id == actor.owner_id,
                    chunk_terms.c.term_hash.in_([key.term(t) for t in tokens])).group_by(chunk_terms.c.chunk_id)
                rows = list(c.execute(base.where(passages.c.id.in_(matching)).limit(1001)).mappings())
                if len(rows) > 1000:
                    raise CloudError('search_requires_narrower_filter', 422)
                ranked = []
                for row in rows:
                    part = key.open('chunk:' + row['id'], row['payload'])
                    words = terms(part['text'])
                    score = sum(min(words.count(token), 4) for token in tokens) / math.sqrt(max(1, len(words)))
                    if score:
                        ranked.append((score, row, part))
            else:
                model = self.embeddings.settings
                rows = list(c.execute(base.join(embeddings, embeddings.c.chunk_id == passages.c.id).where(
                    embeddings.c.owner_id == actor.owner_id, embeddings.c.model == model.embedding_model,
                    embeddings.c.model_revision == model.embedding_revision,
                    embeddings.c.dimensions == model.embedding_dimensions).add_columns(
                        embeddings.c.id.label('embedding_id'), embeddings.c.payload.label('embedding_payload')).limit(1001)).mappings())
                if len(rows) > 1000:
                    raise CloudError('semantic_scan_requires_collection_filter', 422)
                if not rows:
                    raise CloudError('semantic_index_unavailable', 409)
                candidates = [(row['id'], key.open('embedding:' + row['embedding_id'], row['embedding_payload'])) for row in rows]
                distances = self._native(c, vector, candidates)
                ranked = [(1 - distances[row['id']], row, key.open('chunk:' + row['id'], row['payload'])) for row in rows]
            items = []
            for score, row, part in sorted(ranked, key=lambda x: (-x[0], x[1]['id']))[:limit]:
                profile = key.open('document:' + row['document_id'], row['document_profile'])
                items.append(dict(citation_id=citation_id(row['document_id'], row['version'], row['ordinal']),
                    document_id=row['document_id'], collection_id=row['collection_id'], version=row['version'],
                    revision=row['revision'], name=profile['name'], ordinal=row['ordinal'], title=profile.get('title', profile['name']),
                    location=part['location'], excerpt=part['text'], score=round(score, 6), local_only=False))
            return dict(items=items, mode=mode, insufficient_evidence=not items,
                        semantic_strategy='sql_server_native_exact_encrypted_scan' if mode == 'semantic' else None)
