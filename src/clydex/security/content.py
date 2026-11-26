"""Conservative persistence filters, not a claim to recognize every possible secret."""
import re

from clydex.core.errors import PermissionDenied


SECRET_PATTERNS = (
    r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
    r'\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b',
    r'(?i)\bbearer\s+[A-Za-z0-9_.-]{12,}',
    r'(?i)\b(?:password|passphrase|api[_ -]?key|access[_ -]?token|secret[_ -]?key|cvv|pin|bank account)\s*(?::|=|is)\s*\S+',
    r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b',
)


def validate_private_text(value: str, limit: int = 16000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or '\0' in value:
        raise ValueError('Text is empty, invalid or too long.')
    if any(re.search(pattern, value) for pattern in SECRET_PATTERNS):
        raise PermissionDenied('Credential-like content cannot be saved as conversation or memory.')
    for candidate in re.findall(r'(?<!\d)(?:\d[ -]?){13,19}(?!\d)', value):
        digits = re.sub(r'\D', '', candidate)
        if not 13 <= len(digits) <= 19:
            continue
        total = 0
        for i, digit in enumerate(reversed(digits)):
            number = int(digit) * (2 if i % 2 else 1)
            total += number - 9 if number > 9 else number
        if total % 10 == 0:
            raise PermissionDenied('Financial credential-like content cannot be saved.')
    return value.strip()
