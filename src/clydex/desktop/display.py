"""Six views of one native window/Core; geometry is bounded non-secret data."""
import threading
import time
import os

from clydex.core.errors import PermissionDenied
from clydex.core.settings import read_settings, write_settings

MODES = ('window', 'fullscreen', 'widget', 'floating', 'mini', 'tray')
SIZES = {'window': (1360, 900), 'widget': (430, 670), 'floating': (430, 690), 'mini': (800, 240)}


def clamp_geometry(value: dict, area: dict) -> dict:
    expected = {'x', 'y', 'width', 'height'}
    if not isinstance(value, dict) or set(value) != expected or any(type(v) is not int for v in value.values()):
        raise ValueError('Invalid window geometry.')
    width = min(max(340, value['width']), area['width'])
    height = min(max(180, value['height']), area['height'])
    return dict(width=width, height=height,
                x=min(max(area['x'], value['x']), area['x'] + area['width'] - width),
                y=min(max(area['y'], value['y']), area['y'] + area['height'] - height))


class DisplayController:
    def __init__(self, studio, paths, monitor_provider=None):
        self.studio = studio
        self.path = paths.directory('settings') / 'display.json'
        self.window = None
        self.mode, self.monitor = 'window', 0
        self.visible = True
        self._lock = threading.RLock()
        self._changed = 0.
        self._geometry = read_settings(self.path)
        self._monitor_path = paths.directory('settings') / 'display-monitor.json'
        selection = read_settings(self._monitor_path)
        if set(selection) - {'monitor'} or type(selection.get('monitor', 0)) is not int or selection.get('monitor', 0) < 0:
            raise ValueError('Invalid saved monitor preference.')
        self.monitor = selection.get('monitor', 0)
        self._restored = False
        if set(self._geometry) - set(SIZES):
            raise ValueError('Invalid saved display modes.')
        for value in self._geometry.values():
            clamp_geometry(value, dict(x=0, y=0, width=16384, height=16384))
        self._monitor_provider = monitor_provider
        self._full = False

    def monitors(self) -> list[dict]:
        if self._monitor_provider:
            return self._monitor_provider()
        import webview
        result = []
        for index, screen in enumerate(webview.screens):
            result.append(dict(index=index, x=screen.x, y=screen.y, width=screen.width, height=screen.height))
        return result

    def bind(self, window) -> None:
        self.window = window
        window.events.closed += self.studio._close
        window.events.minimized += lambda: self.set_visible(False)
        window.events.shown += lambda: self.set_visible(True)
        window.events.restored += lambda: self.set_visible(True)
        window.events.moved += self.remember
        window.events.resized += self.remember
        window.events.loaded += self.restore_geometry

    def restore_geometry(self) -> None:
        if self._restored or 'window' not in self._geometry:
            return
        self._restored = True
        self._changed = time.monotonic()  # Do not overwrite saved bounds with launch defaults.
        self.change('window')  # Never restore hidden capture or on-top behavior at startup.

    def set_visible(self, visible: bool) -> None:
        self.visible = visible
        self.studio.set_voice_visible(visible)

    def remember(self, *args) -> None:
        if self.window is None or self.mode not in SIZES or not self.visible:
            return
        if time.monotonic() - self._changed < 1:
            return
        areas = self.monitors()
        if not areas:
            return
        try:
            value = dict(x=int(self.window.x), y=int(self.window.y),
                         width=int(self.window.width), height=int(self.window.height))
            # Prefer the actual monitor containing the window, including negative origins.
            area = next((a for a in areas if a['x'] <= value['x'] < a['x'] + a['width']
                         and a['y'] <= value['y'] < a['y'] + a['height']), areas[0])
            self._geometry[self.mode] = clamp_geometry(value, area)
            self.monitor = area['index']
            write_settings(self.path, self._geometry)
            write_settings(self._monitor_path, {'monitor': self.monitor})
            self._changed = time.monotonic()
        except (OSError, ValueError, TypeError):
            pass

    def select_monitor(self, index: int) -> bool:
        areas = self.monitors()
        if type(index) is not int or not 0 <= index < len(areas):
            raise ValueError('Invalid display monitor.')
        self.monitor = index
        write_settings(self._monitor_path, {'monitor': index})
        return self.change(self.mode if self.mode != 'tray' else 'window', reposition=True)

    def _set_on_top(self, enabled: bool) -> None:
        native = getattr(self.window, 'native', None)
        if os.name == 'nt' and native is not None:
            # PyWebView's WinForms setter directly changes TopMost without
            # Invoke. Calling it from a bridge/collector worker can deadlock.
            from System import Action
            native.Invoke(Action(lambda: setattr(self.window, 'on_top', enabled)))
        else:
            self.window.on_top = enabled

    def change(self, mode: str, *, reposition=False) -> bool:
        if mode not in MODES:
            raise ValueError('Invalid display mode.')
        if self.window is None:
            raise RuntimeError('Native window not attached.')
        if self.studio._core.voice.privacy.refresh():
            raise PermissionDenied('Display changes are suspended while locked.')
        if mode == 'tray' and not self.studio._activations.tray_available:
            raise PermissionDenied('Enable the reviewed native tray controls before hiding the window.')
        if self.studio._engine.pending_review() and mode in ('tray', 'mini', 'floating', 'widget'):
            raise PermissionDenied('Review or cancel the pending action before compacting the window.')
        if not reposition:
            self.remember()
        if self._full:
            self.window.toggle_fullscreen()
            self._full = False
        self.mode = mode
        if mode == 'tray':
            self.set_visible(False)
            self.window.hide()
            return True
        self.set_visible(True)
        self.window.show()
        self.window.restore()
        self._set_on_top(mode in ('floating', 'mini'))
        if mode == 'fullscreen':
            self.window.toggle_fullscreen()
            self._full = True
        else:
            areas = self.monitors()
            if not areas:
                raise RuntimeError('No display monitor is available.')
            self.monitor = min(self.monitor, len(areas) - 1)
            area = areas[self.monitor]
            width, height = SIZES[mode]
            value = self._geometry.get(mode, dict(x=area['x'] + 40, y=area['y'] + 40,
                                                  width=width, height=height))
            if reposition:
                value = dict(value, x=area['x'] + 40, y=area['y'] + 40)
            value = clamp_geometry(value, area)
            self.window.resize(value['width'], value['height'])
            self.window.move(value['x'], value['y'])
        return True

    def show_review(self) -> None:
        if self.studio._core.voice.privacy.refresh() or not self.studio._engine.pending_review():
            return
        if self.mode != 'window' or not self.visible:
            self.change('window')

    def snapshot(self) -> dict:
        return dict(mode=self.mode, visible=self.visible, monitor=self.monitor, modes=list(MODES),
                    monitors=self.monitors() if self.window is not None else [])

    def close(self) -> None:
        self.remember()
