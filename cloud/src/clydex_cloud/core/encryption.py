"""Approved server-managed envelope encryption; not end-to-end encryption.

Master/auth keys live separately from SQL and uploaded files. Per-owner keys are
random, wrapped with AES-GCM and bound to owner/version. Backups separately wrap
the key material with an owner-held recovery passphrase.
"""
import hashlib
import hmac
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select, insert

from clydex_cloud.repositories.schema import owner_keys


def encode(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def encrypt(key: bytes, content: bytes, aad: bytes) -> bytes:
    nonce = os.urandom(12)
    return b'CX1' + nonce + AESGCM(key).encrypt(nonce, content, aad)


def decrypt(key: bytes, content: bytes, aad: bytes) -> bytes:
    if not content.startswith(b'CX1') or len(content) < 31:
        raise ValueError('Invalid encrypted envelope.')
    return AESGCM(key).decrypt(content[3:15], content[15:], aad)


class VaultCipher:
    def __init__(self, master_key: bytes, auth_key: bytes):
        if len(master_key) != 32 or len(auth_key) != 32 or master_key == auth_key:
            raise ValueError('Independent 256-bit master and authentication keys are required.')
        self.master_key, self.auth_key = master_key, auth_key

    def new_owner(self, connection, owner: str) -> None:
        aad = f'owner-key:{owner}:1'.encode()
        connection.execute(insert(owner_keys).values(owner_id=owner, key_version=1,
            wrapped_key=encrypt(self.master_key, os.urandom(32), aad)))

    def owner_key(self, connection, owner: str) -> bytes:
        row = connection.execute(select(owner_keys).where(owner_keys.c.owner_id == owner)).mappings().one()
        return decrypt(self.master_key, bytes(row['wrapped_key']), f'owner-key:{owner}:{row["key_version"]}'.encode())

    def seal(self, connection, owner: str, role: str, value) -> bytes:
        return self.owner(connection, owner).seal(role, value)

    def open(self, connection, owner: str, role: str, value: bytes):
        return self.owner(connection, owner).open(role, value)

    def digest(self, role: str, value: str) -> str:
        return hmac.new(self.auth_key, f'{role}:{value}'.encode(), hashlib.sha256).hexdigest()

    def term(self, connection, owner: str, value: str) -> str:
        return self.owner(connection, owner).term(value)

    def owner(self, connection, owner: str) -> 'OwnerCipher':
        return OwnerCipher(self.owner_key(connection, owner), owner)


class OwnerCipher:
    """Ephemeral per-operation key context; no global cross-account key cache."""
    def __init__(self, key: bytes, owner: str):
        self._key, self._owner = key, owner
        self._search_key = hmac.new(key, b'keyword-index-v1', hashlib.sha256).digest()

    def seal(self, role: str, value) -> bytes:
        return encrypt(self._key, encode(value), f'{self._owner}:{role}'.encode())

    def open(self, role: str, value: bytes):
        return json.loads(decrypt(self._key, bytes(value), f'{self._owner}:{role}'.encode()))

    def term(self, value: str) -> str:
        # A blind term index leaks repetition within an owner, not plaintext.
        return hmac.new(self._search_key, value.encode(), hashlib.sha256).hexdigest()
