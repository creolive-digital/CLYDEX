"""One independent cloud runtime; no import/start of the desktop or AI engine."""
from clydex_cloud.authentication.service import Authentication
from clydex_cloud.core.encryption import VaultCipher
from clydex_cloud.devices.service import DeviceService
from clydex_cloud.knowledge.embeddings import LocalEmbeddings
from clydex_cloud.knowledge.retrieval import Retrieval
from clydex_cloud.knowledge.vault import KnowledgeVault
from clydex_cloud.repositories.database import Database
from clydex_cloud.storage.files import FileStorage
from clydex_cloud.synchronization.service import Synchronization
from clydex_cloud.workers.indexing import IndexWorker


class Runtime:
    def __init__(self, settings, *, database=None, cipher=None, parser=None, embedding_service=None):
        if any(x is not None for x in (database, cipher, parser, embedding_service)) and settings.environment != 'test':
            raise ValueError('Injected services are only allowed in explicit tests.')
        self.settings = settings
        if database is None:
            import os
            from clydex_cloud.core.config import outside_source
            if (not settings.database_url_file or settings.database_url_file.is_symlink()
                    or outside_source(settings.database_url_file).stat().st_size > 8192
                    or (os.name != 'nt' and settings.database_url_file.stat().st_mode & 0o077)):
                raise ValueError('A protected database URL file is required.')
            url = settings.database_url_file.read_text().strip()
            database = Database(url)
        self.database = database
        self.cipher = cipher or VaultCipher(settings.secret('master.key'), settings.secret('auth.key'))
        self.authentication = Authentication(database, self.cipher, settings)
        self.devices = DeviceService(database, self.cipher, self.authentication)
        self.synchronization = Synchronization(database, self.cipher, self.authentication)
        self.storage = FileStorage(settings.data_root / 'vault', settings.max_file_bytes)
        self.vault = KnowledgeVault(database, self.cipher, self.authentication, self.storage, self.synchronization, settings)
        self.embeddings = embedding_service or LocalEmbeddings(settings)
        self.retrieval = Retrieval(database, self.cipher, self.embeddings)
        self.worker = IndexWorker(database, self.cipher, self.vault, self.embeddings, **({'parser': parser} if parser else {}))

    def close(self):
        self.worker.close()
        self.worker.wait_closed()
        self.database.close()
