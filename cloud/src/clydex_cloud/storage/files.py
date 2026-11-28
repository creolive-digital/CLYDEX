import hashlib
import os
from pathlib import Path
import tempfile

from clydex.synchronization.contracts import identifier
from clydex_cloud.core.encryption import encrypt, decrypt
from clydex_cloud.core.errors import CloudError


class FileStorage:
    def __init__(self, root: Path, limit: int):
        self.root, self.limit = root.resolve(), limit
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if root.is_symlink():
            raise ValueError('Vault root cannot be a symlink.')

    def path(self, owner: str, object_id: str) -> Path:
        identifier(owner)
        identifier(object_id)
        folder = self.root / owner
        target = folder / (object_id + '.cxb')
        if folder.is_symlink() or target.is_symlink() or self.root not in target.resolve().parents:
            raise CloudError('unsafe_storage_path', 400)
        return target

    def write(self, owner: str, object_id: str, data: bytes, key: bytes) -> str:
        if not 0 < len(data) <= self.limit:
            raise CloudError('file_size_limit', 413)
        encrypted = encrypt(key, data, f'file:{owner}:{object_id}'.encode())
        self.write_encrypted(owner, object_id, encrypted)
        return hashlib.sha256(data).hexdigest()

    def write_encrypted(self, owner: str, object_id: str, content: bytes) -> None:
        target = self.path(owner, object_id)
        if target.exists() or len(content) > self.limit + 64 or not content.startswith(b'CX1'):
            raise CloudError('storage_object_conflict', 409)
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name)
                os.chmod(temporary, 0o600)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            # UUID destinations are internal. Refuse replacement even on a retry.
            os.link(temporary, target)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)

    def read(self, owner: str, object_id: str, key: bytes, sha256: str) -> bytes:
        path = self.path(owner, object_id)
        if not path.is_file() or path.stat().st_size > self.limit + 64:
            raise CloudError('document_content_unavailable', 404)
        try:
            content = decrypt(key, path.read_bytes(), f'file:{owner}:{object_id}'.encode())
        except Exception:
            raise CloudError('content_integrity_failed', 500) from None
        if hashlib.sha256(content).hexdigest() != sha256:
            raise CloudError('content_integrity_failed', 500)
        return content

    def delete(self, owner: str, object_id: str) -> None:
        self.path(owner, object_id).unlink(missing_ok=True)
