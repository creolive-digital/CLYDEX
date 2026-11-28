"""Headless per-user service used by the legacy desktop adapter.

No public listener, no UI import and no automatic cloud/provider startup. The
service owns configuration, persistence, queue and shutdown for one desktop user.
"""
import getpass
import logging
import os
import queue
import threading

from clydex.automation.tasks import SupervisedQueue
from clydex.core.config import AppConfig, RuntimePaths
from clydex.core.errors import PermissionDenied
from clydex.core.legacy_engine import VoiceEngine
from clydex.core.instance import InstanceLock
from clydex.core.logging import configure_logging
from clydex.database.store import LocalStore
from clydex.security.credentials import CredentialStore
from clydex.security.encryption import LocalCipher
from clydex.providers.registry import ProviderRegistry
from clydex.core.orchestrator import IntelligenceCoordinator
from clydex.core.data_actions import OwnedDataActions
from clydex.conversations.repository import ConversationRepository
from clydex.conversations.service import ConversationService
from clydex.memory.repository import MemoryRepository
from clydex.memory.service import MemoryService
from clydex.personality.service import PersonalityService
from clydex.voice.privacy import VoicePrivacy
from clydex.voice.service import VoiceRuntime
from clydex.voice.events import VoiceState
from clydex.cloud.workspace import CloudWorkspace
from clydex.automation.workspace import OperatingWorkspace


def legacy_recognition_mode() -> str | None:
    if os.name != 'nt':
        return None
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\CLYDEX\Voice') as key:
            mode, _ = winreg.QueryValueEx(key, 'RecognitionMode')
            return mode if mode in ('en', 'en-accurate', 'auto') else None
    except OSError:
        return None


class CoreApplication:
    def __init__(self, *, paths=None, config=None, engine=None):
        self.paths = paths or RuntimePaths.for_user()
        self.paths.ensure()
        self._instance = InstanceLock(self.paths.directory('settings') / 'core.lock')
        self._closed = False
        self._shutdown_done = threading.Event()
        self._close_lock = threading.Lock()
        self._shutdown_failure = False
        self._resources = []
        try:
            self.config = config or AppConfig.load(self.paths)
            self.logger = configure_logging(self.paths.directory('logs'))
            self.store = LocalStore(self.paths.directory('data') / 'core.sqlite3')
            self.credentials = CredentialStore()
            self.providers = ProviderRegistry(self.paths, self.credentials)
            owner = getpass.getuser()
            cipher = LocalCipher()
            self.conversations = ConversationService(ConversationRepository(self.store, owner, cipher))
            self.memory = MemoryService(MemoryRepository(self.store, owner, cipher))
            self.conversations.purge_expired()
            self.engine = engine or VoiceEngine(config=self.config, paths=self.paths, store=self.store)
            self.personality = PersonalityService(self.paths, cipher=cipher, owner=owner)
            self.engine.personality = self.personality
            probe = self.engine._voice_privacy_probe
            self.voice = VoiceRuntime(self.paths, self.engine.events.put,
                                      privacy=VoicePrivacy(probe=probe) if probe else None)
            self.engine.voice = self.voice
            self.voice.on_stop = self.stop
            self.voice.on_activation = self.activate_voice
            self.engine.conversation_service = self.conversations
            self.engine.memory_service = self.memory
            self.data_actions = OwnedDataActions(self.engine, self.conversations, self.memory)
            self.engine.data_actions = self.data_actions
            if engine is None:
                self.engine.intelligence = IntelligenceCoordinator(self.providers, self.memory)
            mode = self.store.get_setting('recognition_mode') or legacy_recognition_mode()
            if mode:
                self.engine.speech_mode = mode
            if self.voice.settings.path.exists():
                self.engine.speech_mode = self.voice.config.mode
            else:
                self.voice.settings.config = self.voice.config.__class__(mode=self.engine.speech_mode)
            speak = self.store.get_setting('speak_replies')
            if speak is not None:
                self.engine.speak_preference = speak
            self.queue = SupervisedQueue()
            self.cloud = CloudWorkspace(self, owner, cipher)
            self.register_resource(self.cloud)
            self.operating = OperatingWorkspace(self, owner, cipher)
            self.engine.operating = self.operating
            self.register_resource(self.operating)
            self.voice.start()
            self.logger.info('core_started')
        except Exception:
            self._instance.close()
            self._close_logging()
            raise

    def submit(self, work, *args, only_if_idle=False):
        def perform(token):
            self.engine.cancel_token = token
            with self.voice.foreground(token):
                result = work(*args)
                if not token.is_set() and self.voice.lifecycle.state not in (
                        VoiceState.ERROR, VoiceState.SLEEPING, VoiceState.INTERRUPTED):
                    self.voice.lifecycle.transition(VoiceState.STANDBY)
                return result
        handle = self.queue.submit(perform, only_if_idle=only_if_idle)

        def completed(future):
            if future.cancelled():
                self.engine.events.put(('done', None))
            elif future.exception() is not None:
                self.engine.report_error(future.exception())
                self.engine.events.put(('done', None))
        handle.future.add_done_callback(completed)
        return handle

    def activate_voice(self, source='manual') -> bool:
        if source not in ('manual', 'wake', 'hotkey', 'tray'):
            raise ValueError('Unknown voice activation source.')
        try:
            self.voice.privacy.capture_allowed(self.voice.config)
            self.submit(self.engine.record_worker, None, False, source == 'wake', only_if_idle=True)
            return True
        except (queue.Full, RuntimeError, PermissionDenied):
            return False

    def register_resource(self, service) -> None:
        """Trusted native desktop lifecycles must finish before instance ownership releases."""
        with self._close_lock:
            if self._closed:
                raise RuntimeError('Core is closing.')
            self._resources.append(service)

    def stop(self) -> None:
        if hasattr(self, 'operating'):
            self.operating.stop(clear=self.voice.privacy.locked)
        if self.voice.privacy.locked and hasattr(self, 'cloud'):
            self.cloud.lock()
        self.engine.cancel()
        self.queue.cancel_all()

    def close(self) -> bool:
        with self._close_lock:
            if self._closed:
                return self._shutdown_done.is_set()
            self._closed = True
            self.stop()
            for service in self._resources:
                try:
                    service.close()
                except Exception:
                    self._shutdown_failure = True
                    self.logger.exception('operation_failed')
            try:
                self.engine.close()
            except Exception:
                self._shutdown_failure = True
                self.logger.exception('operation_failed')
            self.queue.close()
            self._finalizer = threading.Thread(target=self._finish_close,
                                               name='clydex-shutdown', daemon=False)
            self._finalizer.start()
        return self._shutdown_done.wait(1)

    def _finish_close(self) -> None:
        try:
            self.queue.wait_closed()
            self.engine.wait_closed()
            for service in self._resources:
                service.wait_closed()
            if self._shutdown_failure:
                raise RuntimeError('Native shutdown failed.')
            self.logger.info('core_stopped')
            self._close_logging()
            self._instance.close()
            self._shutdown_done.set()
        except Exception:
            self.logger.exception('operation_failed')
            self.engine.events.put(('error', 'Core shutdown is incomplete; ownership remains locked.'))
            # Fail closed, including process lifetime, rather than hand native
            # control to a new instance after a failed cleanup.
            threading.Event().wait()

    def wait_closed(self, timeout: float | None = None) -> bool:
        return self._shutdown_done.wait(timeout)

    def _close_logging(self) -> None:
        logger = logging.getLogger('clydex')
        filename = str((self.paths.directory('logs') / 'application.log').resolve())
        for handler in list(logger.handlers):
            if getattr(handler, 'baseFilename', None) == filename:
                logger.removeHandler(handler)
                handler.close()
