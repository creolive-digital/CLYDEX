"""User-bound DPAPI for private local payloads; no plaintext fallback."""
import json
import os

from clydex.core.contracts import canonical_json


class LocalCipher:
    def seal(self, value, owner: str) -> bytes:
        if os.name != 'nt':
            raise RuntimeError('Windows DPAPI is required for persistent private data.')
        import win32crypt
        return win32crypt.CryptProtectData(canonical_json(value).encode('utf-8'), 'CLYDEX local data',
                                           owner.encode('utf-8'), None, None, 0)

    def open(self, value: bytes, owner: str):
        if os.name != 'nt':
            raise RuntimeError('Windows DPAPI is required for persistent private data.')
        import win32crypt
        _, clear = win32crypt.CryptUnprotectData(bytes(value), owner.encode('utf-8'), None, None, 0)
        return json.loads(clear.decode('utf-8'))
