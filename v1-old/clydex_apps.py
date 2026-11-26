"""Named Windows window and accessibility-control operations for the voice agent."""
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import time

import pywintypes
import win32api
import win32con
import win32gui
import win32process


show_window_async = ctypes.windll.user32.ShowWindowAsync
show_window_async.argtypes = (wintypes.HWND, ctypes.c_int)
show_window_async.restype = wintypes.BOOL
get_window_attribute = ctypes.windll.dwmapi.DwmGetWindowAttribute
get_window_attribute.argtypes = (wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD)
get_window_attribute.restype = ctypes.c_long


@dataclass(frozen=True)
class AppWindow:
    hwnd: int
    pid: int
    title: str
    app: str

    def check(self):
        try:
            if (win32gui.IsWindow(self.hwnd) and win32gui.IsWindowVisible(self.hwnd)
                    and win32process.GetWindowThreadProcessId(self.hwnd)[1] == self.pid
                    and win32gui.GetWindowText(self.hwnd) == self.title):
                return
        except pywintypes.error:
            pass
        raise ValueError('That window closed or changed. Ask again using its current title.')


def open_windows():
    handles = []
    win32gui.EnumWindows(lambda hwnd, _: handles.append(hwnd), None)
    windows = []
    for hwnd in handles:
        try:
            if not win32gui.IsWindowVisible(hwnd):
                continue
            cloaked = wintypes.DWORD()
            # DWMWA_CLOAKED includes windows on inactive virtual desktops.
            if get_window_attribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)) == 0 and cloaked.value:
                continue
            if win32gui.GetWindow(hwnd, win32con.GW_OWNER) and win32gui.GetClassName(hwnd) != '#32770':
                continue
            title = win32gui.GetWindowText(hwnd)
            if not title or win32gui.GetClassName(hwnd) in ('Progman', 'WorkerW'):
                continue
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == os.getpid():
                continue
            process = win32api.OpenProcess(
                win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
            try:
                app = Path(win32process.GetModuleFileNameEx(process, 0)).stem
            finally:
                process.Close()
            windows.append(AppWindow(hwnd, pid, title, app))
        except pywintypes.error:
            continue
    return windows


def window_menu(windows):
    return '\n'.join(f'{i}. {w.title} ({w.app})' for i, w in enumerate(windows, 1))


def controls_request(window, mode='inspect', **data):
    window.check()
    if win32gui.IsIconic(window.hwnd):
        raise ValueError(f'Restore “{window.title}” to use its controls.')
    try:
        process = subprocess.run(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
             '-File', str(Path(__file__).with_name('app_controls.ps1'))],
            input=json.dumps(dict(hwnd=window.hwnd, pid=window.pid, title=window.title, mode=mode, **data)),
            text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('The application timed out. Check its window before trying again.') from exc
    if process.returncode:
        raise ValueError('The application could not complete the request. Check for a changed '
                         'control, read-only field, or open dialog in its window.')
    return json.loads(process.stdout)


def control_label(control):
    if control['name']:
        return f"{control['name']} ({control['kind']})"
    return f"{control['kind']} #{control['key']}" if control['key'] else control['kind']


class AppController:
    def __init__(self):
        self.choices = []
        self.last_window = None

    def clear(self):
        self.choices.clear()
        self.last_window = None

    def select(self, target, wait_for_launch):
        key = target.strip().casefold()
        number = re.fullmatch(r'(?:window\s+|#)(\d+)', key)
        if number:
            index = int(number[1]) - 1
            if not 0 <= index < len(self.choices):
                raise ValueError('Ask which windows are open to get their current numbers.')
            window = self.choices[index]
        elif not key:
            if not self.last_window:
                raise ValueError('Which app or window should I control?')
            window = self.last_window
        else:
            app_name = {'file explorer': 'explorer', 'microsoft word': 'winword', 'word': 'winword',
                        'powerpoint': 'powerpnt', 'microsoft edge': 'msedge',
                        'google chrome': 'chrome'}.get(key, key)
            deadline = time.monotonic() + (5 if wait_for_launch else 0)
            while True:
                windows = open_windows()
                matches = [w for w in windows if w.title.casefold() == key]
                if not matches:
                    matches = [w for w in windows if w.app.casefold() == app_name or key in w.title.casefold()]
                if matches or time.monotonic() >= deadline:
                    break
                time.sleep(.2)
            if not matches:
                raise ValueError(f'I could not find an open window matching “{target}”.')
            if len(matches) > 1:
                self.choices = matches
                raise ValueError('Which window? You can say “window 2”, for example.\n' + window_menu(matches))
            window = matches[0]
        window.check()
        self.last_window = window
        return window

    def run(self, action, target, detail, control_name, review, wait_for_launch=False):
        if action == 'list_windows':
            self.choices = open_windows()
            return window_menu(self.choices) or 'I found no open application windows.'
        window = self.select(target, wait_for_launch)
        if action == 'manage_window':
            return self.manage(window, detail, review)
        controls = controls_request(window)
        if action == 'list_controls':
            labels = [control_label(c) for c in controls]
            if not labels:
                return f'“{window.title}” exposes no visible controls I can operate.'
            heading = 'First 60 controls' if len(labels) > 60 else 'Controls'
            return f'{heading} in “{window.title}”:\n' + '\n'.join(labels[:60])
        append = action == 'append_text'
        if append and not detail:
            raise ValueError('What text should I enter?')
        candidates = [c for c in controls if c['editable']] if append else [c for c in controls if c['action']]
        key = control_name.strip().casefold()
        if not append and not key:
            raise ValueError('Name the button or menu item you want me to activate.')
        if key:
            exact = [c for c in candidates if key in (c['name'].casefold(), c['key'].casefold())]
            candidates = exact or [c for c in candidates if key in control_label(c).casefold()]
        if len(candidates) != 1:
            options = ', '.join(f"{control_label(c)} [ID {c['key']}]" if c['key'] else control_label(c)
                                for c in candidates[:8])
            raise ValueError(f'Choose a specific control in “{window.title}”. ' +
                             (f'I found {options}.' if options else 'Ask me to list its controls.'))
        control = candidates[0]
        label = control_label(control)
        description = (f'Append this text to {label} in “{window.title}”?\n\n{detail}' if append
                       else f'Activate {label} in “{window.title}”?')
        if not review(description):
            raise ValueError('Canceled the application action.')
        controls_request(window, 'append' if append else 'press', control=control, text=detail)
        if append:
            try:
                # Editors commonly add an unsaved marker to the same document's title.
                title = win32gui.GetWindowText(window.hwnd)
                if (title.lstrip('*') == window.title.lstrip('*')
                        and win32process.GetWindowThreadProcessId(window.hwnd)[1] == window.pid):
                    self.last_window = AppWindow(window.hwnd, window.pid, title, window.app)
            except pywintypes.error:
                pass  # The edit completed before the window closed.
        return (f'Appended the text to {label} in “{window.title}”.' if append
                else f'Activated {label} in “{window.title}”.')

    @staticmethod
    def manage(window, operation, review):
        hwnd = window.hwnd
        if operation == 'close':
            if not review(f'Close the window “{window.title}”?'):
                raise ValueError('Canceled closing the window.')
            window.check()
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return f'Asked “{window.title}” to close. Its normal save prompts still apply.'
        if operation == 'focus':
            if win32gui.IsIconic(hwnd):
                show_window_async(hwnd, win32con.SW_RESTORE)
                until = time.monotonic() + 1
                while win32gui.IsIconic(hwnd) and time.monotonic() < until:
                    time.sleep(.05)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except pywintypes.error:
                pass
            if win32gui.GetForegroundWindow() != hwnd:
                raise ValueError('Windows kept the current app in front. Select the target from the taskbar.')
            return f'Switched to “{window.title}”.'
        modes = {'minimize': win32con.SW_MINIMIZE, 'maximize': win32con.SW_MAXIMIZE,
                 'restore': win32con.SW_RESTORE}
        if operation not in modes:
            raise ValueError('Choose focus, minimize, maximize, restore, or close.')
        was_minimized = win32gui.IsIconic(hwnd)
        show_window_async(hwnd, modes[operation])
        until = time.monotonic() + 2
        states = {'minimize': win32con.SW_SHOWMINIMIZED, 'maximize': win32con.SW_SHOWMAXIMIZED,
                  'restore': win32con.SW_SHOWNORMAL}
        allowed = {states[operation]}
        if operation == 'restore' and was_minimized:
            allowed.add(win32con.SW_SHOWMAXIMIZED)
        while win32gui.GetWindowPlacement(hwnd)[1] not in allowed:
            if time.monotonic() >= until:
                raise ValueError(f'The window did not confirm the request to {operation}.')
            time.sleep(.05)
        return f'Window {operation}d: “{window.title}”.'
