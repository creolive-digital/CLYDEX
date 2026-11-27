"""Trusted opt-in activation adapters; all requests return to the same Core queue."""
import threading

from clydex.core.errors import Cancelled
from clydex.desktop.hotkeys import GlobalHotkey
from clydex.desktop.tray import SystemTray


class DesktopActivations:
    def __init__(self, actions, hotkey_factory=GlobalHotkey, tray_factory=SystemTray):
        self.actions, self.hotkey_factory, self.tray_factory = actions, hotkey_factory, tray_factory
        self._services, self._lock, self._closed = [], threading.RLock(), threading.Event()
        self.status = {'hotkey': 'off', 'tray': 'off'}

    def configure(self, config, cancel):
        with self._lock:
            previous = list(self._services)
        for service in previous:
            service.close()
            service.wait_closed()
        with self._lock:
            self._services.clear()
        if self._closed.is_set():
            raise Cancelled('Desktop activations are closing.')
        cancel.check()
        desired = []
        if config.hotkey_enabled:
            desired.append(('hotkey', self.hotkey_factory(config.hotkey, self.actions['hotkey'])))
        if config.tray_enabled:
            desired.append(('tray', self.tray_factory(self.actions)))
        try:
            self.status = {'hotkey': 'off', 'tray': 'off'}
            for key, service in desired:
                with self._lock:
                    if self._closed.is_set():
                        raise Cancelled('Desktop activations are closing.')
                    self._services.append(service)
                cancel.check()
                service.start()
                cancel.check()
                if self._closed.is_set():
                    raise Cancelled('Desktop activations are closing.')
                self.status[key] = service.status
        except Exception:
            for _, service in desired:
                service.close()
                service.wait_closed()
            self.status = {'hotkey': 'unavailable', 'tray': 'unavailable'}
            raise

    def update(self, voice):
        with self._lock:
            for service in self._services:
                if isinstance(service, SystemTray):
                    label = 'muted' if voice['muted'] else voice['wake_status'] if voice['background_armed'] else voice['state']
                    service.update('CLYDEX — microphone ' + label)

    @property
    def tray_available(self) -> bool:
        with self._lock:
            return any(isinstance(service, SystemTray) and service.status == 'active' for service in self._services)

    def close(self):
        self._closed.set()
        with self._lock:
            for service in self._services:
                service.close()

    def wait_closed(self):
        with self._lock:
            services = list(self._services)
        for service in services:
            service.wait_closed()
