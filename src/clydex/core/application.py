"""Headless per-user service used by the legacy desktop adapter.

No public listener, no UI import and no automatic cloud/provider startup. The
service owns configuration, persistence, queue and shutdown for one desktop user.
"""
import logging
import os
import threading

from clydex.automation.tasks import SupervisedQueue
from clydex.core.config import AppConfig, RuntimePaths
from clydex.core.legacy_engine import VoiceEngine
from clydex.core.instance import InstanceLock
from clydex.core.logging import configure_logging
from clydex.database.store import LocalStore
from clydex.security.credentials import CredentialStore


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
        try:
            self.config = config or AppConfig.load(self.paths)
            self.logger = configure_logging(self.paths.directory('logs'))
            self.store = LocalStore(self.paths.directory('data') / 'core.sqlite3')
            self.credentials = CredentialStore()
            self.engine = engine or VoiceEngine(config=self.config, paths=self.paths, store=self.store)
            mode = self.store.get_setting('recognition_mode') or legacy_recognition_mode()
            if mode:
                self.engine.speech_mode = mode
            speak = self.store.get_setting('speak_replies')
            if speak is not None:
                self.engine.speak_preference = speak
            self.queue = SupervisedQueue()
            self.logger.info('core_started')
        except Exception:
            self._instance.close()
            self._close_logging()
            raise

    def submit(self, work, *args):
        def perform(token):
            self.engine.cancel_token = token
            return work(*args)
        handle = self.queue.submit(perform)

        def completed(future):
            if future.cancelled():
                self.engine.events.put(('done', None))
            elif future.exception() is not None:
                self.engine.report_error(future.exception())
                self.engine.events.put(('done', None))
        handle.future.add_done_callback(completed)
        return handle

    def stop(self) -> None:
        self.engine.cancel()
        self.queue.cancel_all()

    def close(self) -> bool:
        with self._close_lock:
            if self._closed:
                return self._shutdown_done.is_set()
            self._closed = True
            self.stop()
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
