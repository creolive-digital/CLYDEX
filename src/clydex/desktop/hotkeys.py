"""Explicit Windows RegisterHotKey lifecycle; no unrestricted keyboard hook."""
import threading

from clydex.core.errors import SpeechInputError


def parse_hotkey(value: str) -> tuple[int, int]:
    if not isinstance(value, str) or len(value) > 80:
        raise ValueError('Invalid shortcut.')
    *modifiers, key = value.split('+')
    flags = {'ALT': 1, 'CTRL': 2, 'SHIFT': 4, 'WIN': 8}
    if not modifiers or len(set(modifiers)) != len(modifiers) or any(m not in flags for m in modifiers):
        raise ValueError('Choose distinct shortcut modifiers.')
    if 'WIN' in modifiers or key == 'F12':
        raise ValueError('Windows-key shortcuts and F12 are reserved by the operating system.')
    if key == 'SPACE':
        code = 32
    elif len(key) == 1 and key.isascii() and key.isalnum() and key == key.upper():
        code = ord(key)
    elif key.startswith('F') and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        code = 0x70 + int(key[1:]) - 1
    else:
        raise ValueError('Choose a letter, digit, Space or F1–F24.')
    return sum(flags[m] for m in modifiers) | 0x4000, code  # MOD_NOREPEAT.


class GlobalHotkey:
    def __init__(self, shortcut: str, callback):
        self.flags, self.key = parse_hotkey(shortcut)
        self.callback = callback
        self._stop, self._ready = threading.Event(), threading.Event()
        self._thread, self.status = None, 'off'

    def start(self):
        if self._thread:
            raise RuntimeError('Shortcut is already registered or closing.')
        self._thread = threading.Thread(target=self._run, name='clydex-hotkey', daemon=True)
        self._thread.start()
        if not self._ready.wait(3) or self.status != 'registered':
            self.close()
            raise SpeechInputError('Shortcut is reserved, already used or unavailable on this desktop.')

    def _run(self):
        registered = False
        try:
            import ctypes
            from ctypes import wintypes
            user = ctypes.WinDLL('user32', use_last_error=True)
            user.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
            user.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
            user.PeekMessageW.argtypes = (ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT)
            if self._stop.is_set():
                return
            registered = bool(user.RegisterHotKey(None, 0xC1D, self.flags, self.key))
            self.status = 'registered' if registered else 'unavailable'
            self._ready.set()
            message = wintypes.MSG()
            while registered and not self._stop.wait(.02):
                while user.PeekMessageW(ctypes.byref(message), None, 0, 0, 1):
                    if message.message == 0x312 and message.wParam == 0xC1D and not self._stop.is_set():
                        self.callback()
        except Exception:
            self.status = 'unavailable'
        finally:
            if registered:
                user.UnregisterHotKey(None, 0xC1D)
            self._ready.set()
            if self.status == 'registered':
                self.status = 'off'

    def close(self):
        self._stop.set()

    def wait_closed(self):
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join()
