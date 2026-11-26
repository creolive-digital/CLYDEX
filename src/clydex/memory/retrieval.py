"""Bounded lexical retrieval; no embeddings, model calls or cloud synchronization."""
import re


def retrieve(records: list[dict], query: str, limit: int = 5) -> list[dict]:
    words = {word for word in re.findall(r'\w+', query.casefold()) if len(word) >= 3}
    ranked = []
    for record in records:
        if not record['confirmed'] or record['status'] != 'active':
            continue
        tokens = set(re.findall(r'\w+', record['value'].casefold()))
        score = len(words & tokens)
        if score:
            ranked.append((score, record['updated_at'], record))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [{key: record[key] for key in ('id', 'category', 'value', 'origin', 'confirmed', 'local_only')}
            for _, _, record in ranked[:limit]]
