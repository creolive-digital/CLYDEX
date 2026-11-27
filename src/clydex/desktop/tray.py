"""Opt-in native tray controls with a joined, Core-owned Windows message thread."""
import threading
import time
import uuid

from clydex.core.errors import SpeechInputError


class SystemTray:
    def __init__(self, actions: dict):
        self.actions = actions
        self._stop, self._ready = threading.Event(), threading.Event()
        self._thread, self._window = None, None
        self.status, self._tooltip = 'off', 'CLYDEX — microphone muted'

    def start(self):
        self._thread = threading.Thread(target=self._run, name='clydex-tray', daemon=True)
        self._thread.start()
        if not self._ready.wait(3) or self.status != 'active':
            self.close()
            raise SpeechInputError('System tray is unavailable on this Windows desktop.')

    def _run(self):
        icon_added, class_registered, class_name, instance = False, False, 'CLYDEXTray_' + uuid.uuid4().hex, None
        try:
            import win32api
            import win32con
            import win32gui
            instance = win32api.GetModuleHandle(None)
            def procedure(hwnd, message, wparam, lparam):
                if message == win32con.WM_USER + 20:
                    event = lparam & 0xffff  # NOTIFYICON_VERSION_4 packs icon ID in the high word.
                    if event in (win32con.WM_LBUTTONDBLCLK, 0x400, 0x401):  # NIN_SELECT / NIN_KEYSELECT.
                        self.actions['open']()
                    elif event in (win32con.WM_RBUTTONUP, win32con.WM_CONTEXTMENU):
                        menu = win32gui.CreatePopupMenu()
                        try:
                            labels = [('Open CLYDEX', 'open'), ('Talk / interrupt', 'activate'),
                                      ('Mute microphone', 'mute'), ('Unmute microphone this session', 'unmute'),
                                      ('Stop task', 'stop'), ('Exit', 'exit')]
                            for number, (label, _) in enumerate(labels, 1):
                                win32gui.AppendMenu(menu, win32con.MF_STRING, number, label)
                            win32gui.SetForegroundWindow(hwnd)
                            x, y = win32gui.GetCursorPos()
                            selected = win32gui.TrackPopupMenu(menu, win32con.TPM_RETURNCMD | win32con.TPM_RIGHTBUTTON,
                                                               x, y, 0, hwnd, None)
                            if 1 <= selected <= len(labels):
                                self.actions[labels[selected - 1][1]]()
                            win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
                        finally:
                            win32gui.DestroyMenu(menu)
                    return 0
                return win32gui.DefWindowProc(hwnd, message, wparam, lparam)
            wc = win32gui.WNDCLASS()
            wc.hInstance, wc.lpszClassName, wc.lpfnWndProc = instance, class_name, procedure
            win32gui.RegisterClass(wc)
            class_registered = True
            self._window = win32gui.CreateWindow(class_name, 'CLYDEX', 0, 0, 0, 0, 0, 0, 0, instance, None)
            # Neutral OS fallback icon, not replacement CLYDEX production artwork.
            icon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, (self._window, 0, 0x80 | win32gui.NIF_ICON | win32gui.NIF_MESSAGE |
                win32gui.NIF_TIP, win32con.WM_USER + 20, icon, self._tooltip))
            # Pywin32 tuple field 7 maps the uTimeout/uVersion union.
            win32gui.Shell_NotifyIcon(win32gui.NIM_SETVERSION, (self._window, 0, 0, 0, 0, '', '', 4))
            icon_added, self.status = True, 'active'
            self._ready.set()
            last_update = 0.
            while not self._stop.wait(.02):
                win32gui.PumpWaitingMessages()
                if 'voice_status' in self.actions and time.monotonic() - last_update >= .2:
                    last_update = time.monotonic()
                    voice = self.actions['voice_status']()
                    label = 'muted' if voice['muted'] else voice['wake_status'] if voice['background_armed'] else voice['state']
                    self.update('CLYDEX — microphone ' + label)
        except Exception:
            self.status = 'unavailable'
        finally:
            try:
                if self._window:
                    try:
                        if icon_added:
                            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self._window, 0))
                    finally:
                        win32gui.DestroyWindow(self._window)
                        self._window = None
                if class_registered:
                    win32gui.UnregisterClass(class_name, instance)
            finally:
                self._ready.set()
                if self.status == 'active':
                    self.status = 'off'

    def update(self, text: str):
        text = text[:100]
        if text != self._tooltip and self._window:
            self._tooltip = text
            try:
                import win32gui
                win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, (self._window, 0, win32gui.NIF_TIP | 0x80, 0, 0, text))
            except Exception:
                self.status = 'unavailable'

    def close(self):
        self._stop.set()

    def wait_closed(self):
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join()
