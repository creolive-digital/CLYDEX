"""Quiet isolated frozen Windows startup/close; no audio, providers or private profile."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import time


def main(executable, output):
    profile = output / 'frozen-profile'
    profile.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, LOCALAPPDATA=str(profile), CLYDEX_ALLOW_CLOUD='false')
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    process = subprocess.Popen([str(executable), '--silent', '--reduced-motion'], env=env, startupinfo=startup)
    user = ctypes.WinDLL('user32', use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    user.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
    user.PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    found = []
    @callback_type
    def inspect(window, param):
        pid = wintypes.DWORD()
        user.GetWindowThreadProcessId(window, ctypes.byref(pid))
        if pid.value == process.pid:
            title = ctypes.create_unicode_buffer(256)
            user.GetWindowTextW(window, title, 256)
            if title.value.startswith('CLYDEX'):
                user.ShowWindow(window, 0)
                found.append(window)
        return True
    started = time.monotonic()
    try:
        while not found and process.poll() is None and time.monotonic() - started < 30:
            user.EnumWindows(inspect, 0)
            time.sleep(.05)
        if not found:
            raise RuntimeError('Frozen CLYDEX window did not initialize.')
        time.sleep(2)
        user.PostMessageW(found[0], 0x0010, 0, 0)
        code = process.wait(20)
        log = profile / 'CLYDEX/logs/application.log'
        events = [json.loads(line)['event'] for line in log.read_text().splitlines()]
        result = dict(window_initialized=True, exit_code=code, core_started='core_started' in events,
                      core_stopped='core_stopped' in events, cloud_disabled=True,
                      elapsed_seconds=round(time.monotonic()-started, 3),
                      limits='Frozen native window/startup/clean shutdown only; no DOM, network, audio or installer acceptance')
        (output / 'frozen-native-results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        if code or not result['core_stopped']:
            raise RuntimeError('Frozen shutdown did not complete.')
        return result
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    print(json.dumps(main(args.executable.resolve(), args.output.resolve()), indent=2))
