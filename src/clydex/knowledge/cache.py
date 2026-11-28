"""Selected excerpts only, DPAPI encrypted and account bound; no raw audio cache."""
import time
from clydex.core.contracts import canonical_json
from clydex.knowledge.models import terms
from clydex.synchronization.contracts import identifier


class KnowledgeCache:
    def __init__(self, sync, *, clock=time.time):
        self.sync, self.clock = sync, clock

    def purge(self, binding, document_id=None):
        with self.sync.store.connect() as c:
            c.execute('DELETE FROM knowledge_cache WHERE owner=? AND binding=?' + (' AND document_id=?' if document_id else ''),
                      (self.sync.owner, binding, document_id) if document_id else (self.sync.owner, binding))

    def put(self, binding, document_id, items, *, hours=24, quota_bytes=10 * 1024 * 1024):
        identifier(document_id)
        if (type(hours) is not int or not 1 <= hours <= 720 or type(quota_bytes) is not int
                or not 65536 <= quota_bytes <= 50 * 1024 * 1024 or not isinstance(items, list) or not 1 <= len(items) <= 2000):
            raise ValueError('Invalid offline cache limits.')
        version, revision = items[0]['version'], items[0]['revision']
        for item in items:
            if (item['document_id'] != document_id or item['version'] != version or item['revision'] != revision
                    or not isinstance(item['excerpt'], str) or not 0 < len(item['excerpt']) <= 2000
                    or len(item['location']) > 200 or len(item['name']) > 180):
                raise ValueError('Inconsistent or invalid cached excerpts.')
        size = len(canonical_json(items).encode())
        if size > 4 * 1024 * 1024:
            raise ValueError('Document excerpt cache exceeds its 4 MiB bound.')
        encrypted = self.sync.seal(binding, 'cache:' + document_id, items)
        with self.sync.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('DELETE FROM knowledge_cache WHERE owner=? AND binding=? AND (expires<=? OR document_id=?)',
                      (self.sync.owner, binding, self.clock(), document_id))
            used = c.execute('SELECT coalesce(sum(size_bytes),0) FROM knowledge_cache WHERE owner=? AND binding=?',
                             (self.sync.owner, binding)).fetchone()[0]
            if used + len(encrypted) > quota_bytes:
                raise ValueError('Offline cache quota reached; remove selected documents first.')
            c.execute('INSERT INTO knowledge_cache VALUES(?,?,?,?,?,?,?)', (self.sync.owner, binding, document_id,
                revision, self.clock() + hours * 3600, len(encrypted), encrypted))
        return {'cached': True, 'document_id': document_id, 'excerpt_count': len(items)}

    def snapshot(self, binding):
        with self.sync.store.connect() as c:
            c.execute('DELETE FROM knowledge_cache WHERE owner=? AND binding=? AND expires<=?', (self.sync.owner, binding, self.clock()))
            rows = c.execute('SELECT document_id,revision,expires,size_bytes FROM knowledge_cache WHERE owner=? AND binding=?',
                             (self.sync.owner, binding)).fetchall()
        return {'items': [dict(zip(('document_id', 'revision', 'expires', 'size_bytes'), r)) for r in rows],
                'size_bytes': sum(r[3] for r in rows), 'revocation': 'Checked when connected; unavailable to a disconnected device.'}

    def search(self, binding, query, limit=5):
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 1000 or not 1 <= limit <= 20:
            raise ValueError('Invalid offline query.')
        self.snapshot(binding)
        with self.sync.store.connect() as c:
            rows = c.execute('SELECT document_id,payload FROM knowledge_cache WHERE owner=? AND binding=? AND expires>?',
                             (self.sync.owner, binding, self.clock())).fetchall()
        query_terms = set(terms(query)[:16])
        ranked = []
        for key, blob in rows:
            for item in self.sync.open(binding, 'cache:' + key, blob):
                score = len(query_terms & set(terms(item['excerpt'])))
                if score:
                    ranked.append(dict(item, score=score))
        ranked.sort(key=lambda x: (-x['score'], x['citation_id']))
        return dict(items=ranked[:limit], mode='offline_keyword', insufficient_evidence=not ranked)
