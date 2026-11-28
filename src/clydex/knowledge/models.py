"""Bounded, transport-independent source passages and citation contracts."""
from dataclasses import asdict, dataclass
import hashlib
import re
import unicodedata


def normalized(value: str) -> str:
    return unicodedata.normalize('NFKC', value).replace('\x00', '').strip()


def terms(value: str) -> list[str]:
    result, word = [], []
    for char in normalized(value).casefold()[:200000]:
        if unicodedata.category(char)[0] in ('L', 'N', 'M'):
            word.append(char)
        elif word:
            result.append(''.join(word)[:100])
            word = []
    if word:
        result.append(''.join(word)[:100])
    return result


@dataclass(frozen=True)
class Passage:
    text: str
    location: str
    ordinal: int

    def __post_init__(self):
        if not 0 < len(self.text) <= 2000 or not 0 < len(self.location) <= 200 or self.ordinal < 0:
            raise ValueError('Invalid bounded passage.')

    def public(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Extraction:
    status: str
    parser: str
    passages: tuple[Passage, ...] = ()
    warning: str = ''

    def public(self) -> dict:
        return dict(status=self.status, parser=self.parser, passages=[p.public() for p in self.passages],
                    warning=self.warning)


def chunks(text: str, location: str, start: int = 0, *, size: int = 900, overlap: int = 120) -> list[Passage]:
    text = normalized(re.sub(r'[ \t]+', ' ', text))
    if len(text) > 1_000_000 or not 100 <= size <= 1800 or not 0 <= overlap < size // 2:
        raise ValueError('Extraction bounds exceeded.')
    result = []
    for offset in range(0, len(text), size - overlap):
        part = text[offset:offset + size].strip()
        if part:
            result.append(Passage(part, f'{location}; characters {offset + 1}–{offset + len(part)}',
                                  start + len(result)))
    return result


def citation_id(document_id: str, version: int, ordinal: int) -> str:
    value = f'{document_id}:{version}:{ordinal}'
    return 'K-' + hashlib.sha256(value.encode()).hexdigest()[:16]
