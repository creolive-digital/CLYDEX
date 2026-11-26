"""Cancellable subprocess helper; no shell expansion and bounded execution time."""
import os
import signal
import subprocess
import time

from clydex.core.contracts import Cancellation
from clydex.core.errors import Cancelled


def run_process(args: list[str], *, input: str, cwd, timeout: float,
                cancel: Cancellation) -> subprocess.CompletedProcess:
    if cancel.is_set():
        raise Cancelled('Process canceled before launch.')
    process = subprocess.Popen(
        args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding='utf-8', errors='replace',
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), start_new_session=os.name != 'nt')
    deadline = time.monotonic() + timeout
    first = True
    try:
        while True:
            if cancel.is_set():
                raise Cancelled('Process canceled; earlier effects may remain.')
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(args, timeout)
            try:
                output, errors = process.communicate(input=input if first else None, timeout=.1)
                return subprocess.CompletedProcess(args, process.returncode, output, errors)
            except subprocess.TimeoutExpired:
                first = False
    finally:
        if process.poll() is None:
            if os.name == 'nt':
                try:
                    subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                                   capture_output=True, timeout=5,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                except (OSError, subprocess.TimeoutExpired):
                    pass  # Still terminate the immediate child if tree termination fails.
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.kill()
        try:
            process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            # A surviving external process may hold an inherited pipe open.
            for pipe in (process.stdin, process.stdout, process.stderr):
                if pipe:
                    pipe.close()
