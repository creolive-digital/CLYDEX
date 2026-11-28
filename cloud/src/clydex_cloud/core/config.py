"""Fail-closed cloud configuration; secrets are files outside database/vault/source."""
from dataclasses import dataclass
import os
from pathlib import Path


def outside_source(path: Path) -> Path:
    if not path.is_absolute():
        raise ValueError('Runtime paths must be absolute.')
    result = path.resolve()
    source = Path(__file__).resolve().parents[4]
    if result == source or source in result.parents:
        raise ValueError('Cloud runtime data cannot be inside source.')
    return result


@dataclass(frozen=True)
class Settings:
    data_root: Path
    secrets_root: Path
    database_url_file: Path | None = None
    environment: str = 'production'
    registration_enabled: bool = False
    public_host: str = 'localhost'
    require_tls: bool = True
    docs_enabled: bool = False
    inline_workers: int = 0
    quota_bytes: int = 100 * 1024 * 1024
    max_file_bytes: int = 10 * 1024 * 1024
    access_seconds: int = 300
    refresh_seconds: int = 30 * 86400
    request_limit: int = 120
    audit_retention_days: int = 0
    embedding_model: str = ''
    embedding_revision: str = ''
    embedding_dimensions: int = 0
    embedding_license: str = ''
    local_embeddings_confirmed: bool = False

    def __post_init__(self):
        data, keys = outside_source(self.data_root), outside_source(self.secrets_root)
        if data == keys or data in keys.parents or keys in data.parents:
            raise ValueError('Secrets and cloud data need separate directories.')
        if self.environment not in ('production', 'development', 'test'):
            raise ValueError('Invalid runtime environment.')
        if self.environment == 'production' and not self.require_tls:
            raise ValueError('Production requires transport encryption.')
        if (not self.public_host or any(x in self.public_host for x in '/:@*')
                or not 0 <= self.inline_workers <= 4 or not 1 <= self.request_limit <= 10000
                or not 1024 <= self.max_file_bytes <= 10 * 1024 * 1024
                or not self.max_file_bytes <= self.quota_bytes <= 100 * 1024**3
                or not 60 <= self.access_seconds <= 900 or not 3600 <= self.refresh_seconds <= 90 * 86400
                or not 0 <= self.audit_retention_days <= 3650):
            raise ValueError('Cloud configuration exceeds allowed bounds.')
        if self.embedding_model and (not self.local_embeddings_confirmed or not self.embedding_revision
                or not self.embedding_license or not 1 <= self.embedding_dimensions <= 1998
                or ':cloud' in self.embedding_model.casefold()):
            raise ValueError('Embeddings require an explicitly licensed/versioned local model.')

    @classmethod
    def from_environment(cls) -> 'Settings':
        def flag(name, default=False):
            value = os.environ.get('CLYDEX_' + name, str(default)).lower()
            if value not in ('true', 'false'):
                raise ValueError('Boolean environment configuration must be true/false.')
            return value == 'true'
        return cls(data_root=Path(os.environ.get('CLYDEX_DATA_ROOT', '/var/lib/clydex')),
            secrets_root=Path(os.environ.get('CLYDEX_SECRETS_ROOT', '/run/secrets/clydex')),
            database_url_file=Path(os.environ['CLYDEX_DATABASE_URL_FILE']) if 'CLYDEX_DATABASE_URL_FILE' in os.environ else None,
            environment=os.environ.get('CLYDEX_ENVIRONMENT', 'production'),
            public_host=os.environ.get('CLYDEX_PUBLIC_HOST', 'localhost'),
            registration_enabled=flag('REGISTRATION_ENABLED'), require_tls=flag('REQUIRE_TLS', True),
            docs_enabled=flag('DOCS_ENABLED'), inline_workers=int(os.environ.get('CLYDEX_INLINE_WORKERS', '0')),
            audit_retention_days=int(os.environ.get('CLYDEX_AUDIT_RETENTION_DAYS', '0')),
            quota_bytes=int(os.environ.get('CLYDEX_QUOTA_BYTES', str(100 * 1024 * 1024))),
            embedding_model=os.environ.get('CLYDEX_EMBEDDING_MODEL', ''),
            embedding_revision=os.environ.get('CLYDEX_EMBEDDING_REVISION', ''),
            embedding_dimensions=int(os.environ.get('CLYDEX_EMBEDDING_DIMENSIONS', '0')),
            embedding_license=os.environ.get('CLYDEX_EMBEDDING_LICENSE', ''),
            local_embeddings_confirmed=flag('LOCAL_EMBEDDINGS_CONFIRMED'))

    def secret(self, name: str, length: int = 32) -> bytes:
        if name not in ('master.key', 'auth.key', 'registration.key'):
            raise ValueError('Unknown secret role.')
        path = self.secrets_root / name
        if path.is_symlink():
            raise ValueError('Secret symlinks are not accepted.')
        value = path.read_bytes()
        if len(value) != length or (os.name != 'nt' and path.stat().st_mode & 0o077):
            raise ValueError('Invalid secret length or permissions.')
        return value
