"""Fail-closed microphone/session policy, independent of frontend and model text."""
import os
import threading

from clydex.core.errors import Cancelled, PermissionDenied


def desktop_locked() -> bool:
    if os.name != 'nt':
        return True
    import win32ts
    # OpenInputDesktop alone can return the reconnect desktop for a disconnected
    # RDP session. Such a session must not keep listening or speaking.
    state = win32ts.WTSQuerySessionInformation(win32ts.WTS_CURRENT_SERVER_HANDLE,
                                              win32ts.WTS_CURRENT_SESSION, win32ts.WTSConnectState)
    if state != win32ts.WTSActive:
        return True
    import ctypes
    from ctypes import wintypes
    user = ctypes.WinDLL('user32', use_last_error=True)
    user.OpenInputDesktop.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    user.OpenInputDesktop.restype = wintypes.HANDLE
    user.CloseDesktop.argtypes = (wintypes.HANDLE,)
    user.GetUserObjectInformationW.argtypes = (wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID,
                                               wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))
    desktop = user.OpenInputDesktop(0, False, 1)
    if not desktop:
        return True
    try:
        name, needed = ctypes.create_unicode_buffer(256), wintypes.DWORD()
        return (not user.GetUserObjectInformationW(desktop, 2, name, ctypes.sizeof(name), ctypes.byref(needed))
                or name.value.casefold() != 'default')
    finally:
        user.CloseDesktop(desktop)


def require_active(cancel, guard) -> None:
    if cancel.is_set():
        raise Cancelled('Voice operation interrupted.')
    guard()


class VoicePrivacy:
    def __init__(self, probe=desktop_locked, on_lock=None):
        self.probe, self.on_lock = probe, on_lock
        self.muted, self.visible, self.locked = True, True, False
        self._lock = threading.RLock()
        self.background_indicator = lambda: False

    def refresh(self) -> bool:
        try:
            locked = bool(self.probe())
        except Exception:
            locked = True
        with self._lock:
            changed = locked and not self.locked
            self.locked = locked
            if locked:
                self.muted = True
        if changed and self.on_lock:
            self.on_lock()
        return locked

    def unmute(self, config) -> None:
        if self.refresh() or not config.microphone_enabled:
            raise PermissionDenied('Enable microphone policy and unlock the desktop before unmuting.')
        with self._lock:
            self.muted = False

    def capture_allowed(self, config) -> None:
        if self.refresh():
            raise PermissionDenied('Microphone capture is suspended on the lock/secure desktop.')
        with self._lock:
            if (not config.microphone_enabled or self.muted
                    or (not self.visible and (not config.background_listening or not self.background_indicator()))):
                raise PermissionDenied('Microphone is muted, disabled or disallowed in the background.')

    def output_allowed(self, config) -> None:
        if self.refresh() or (not self.visible and (not config.background_listening or not self.background_indicator())):
            raise PermissionDenied('Speech output is suspended by local privacy policy.')
