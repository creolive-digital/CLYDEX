"""Bounded child I/O, deadlines, cancellation and owned-process-tree cleanup."""
import os
import signal
import subprocess
import threading
import time

from clydex.core.contracts import Cancellation
from clydex.core.errors import Cancelled, ClydexError


def _resume_owned_process(pid: int) -> None:
    """Resume only the newly suspended process, after its job assignment.

    Tool Help thread enumeration avoids relying on undocumented NT functions.
    https://learn.microsoft.com/windows/win32/toolhelp/traversing-the-thread-list
    """
    import ctypes
    from ctypes import wintypes
    class ThreadEntry(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('usage', wintypes.DWORD),
                    ('tid', wintypes.DWORD), ('pid', wintypes.DWORD),
                    ('priority', wintypes.LONG), ('delta', wintypes.LONG), ('flags', wintypes.DWORD)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Thread32First.argtypes = (wintypes.HANDLE, ctypes.POINTER(ThreadEntry))
    kernel.Thread32Next.argtypes = kernel.Thread32First.argtypes
    kernel.OpenThread.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenThread.restype = wintypes.HANDLE
    kernel.ResumeThread.argtypes = (wintypes.HANDLE,)
    kernel.ResumeThread.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    snapshot = kernel.CreateToolhelp32Snapshot(4, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise OSError('Cannot enumerate the owned process thread.')
    try:
        entry = ThreadEntry()
        entry.size = ctypes.sizeof(entry)
        present = kernel.Thread32First(snapshot, ctypes.byref(entry))
        while present:
            if entry.pid == pid:
                thread = kernel.OpenThread(2, False, entry.tid)
                if not thread:
                    raise OSError('Cannot open the owned process thread.')
                try:
                    if kernel.ResumeThread(thread) == 0xFFFFFFFF:
                        raise OSError('Cannot resume the owned process.')
                    return
                finally:
                    kernel.CloseHandle(thread)
            present = kernel.Thread32Next(snapshot, ctypes.byref(entry))
        raise OSError('Owned process thread unavailable.')
    finally:
        kernel.CloseHandle(snapshot)


class OutputLimitExceeded(ClydexError):
    code = 'output_limit'


def run_process(args: list[str], *, input: str, cwd, timeout: float,
                cancel: Cancellation, max_output_bytes: int = 1_048_576,
                watch_files: tuple = ()) -> subprocess.CompletedProcess:
    if cancel.is_set():
        raise Cancelled('Process canceled before launch.')
    encoded = input.encode('utf-8')
    if len(encoded) > 1_048_576 or not 0 < timeout <= 900 or max_output_bytes < 1:
        raise ValueError('Invalid process input or limits.')
    process = subprocess.Popen(
        args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=(getattr(subprocess, 'CREATE_NO_WINDOW', 0) | (4 if os.name == 'nt' else 0)),
        start_new_session=os.name != 'nt')
    job = None
    assigned = False
    workers = []
    try:
        if os.name == 'nt':
            import win32job
            job = win32job.CreateJobObject(None, '')
            info = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
            info['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, info)
            win32job.AssignProcessToJobObject(job, int(process._handle))
            assigned = True
            _resume_owned_process(process.pid)
        overflow = threading.Event()
        guard = threading.Lock()
        total = 0
        captured = [bytearray(), bytearray()]

        def drain(pipe, index):
            nonlocal total
            try:
                while chunk := pipe.read1(8192):
                    with guard:
                        total += len(chunk)
                        if total > max_output_bytes:
                            overflow.set()
                        else:
                            captured[index].extend(chunk)
            except OSError:
                pass

        def write():
            try:
                process.stdin.write(encoded)
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            finally:
                process.stdin.close()

        for function, arguments in ((drain, (process.stdout, 0)), (drain, (process.stderr, 1)), (write, ())):
            thread = threading.Thread(target=function, args=arguments, daemon=True)
            workers.append(thread)
            thread.start()
        deadline = time.monotonic() + timeout
        while True:
            if cancel.is_set():
                raise Cancelled('Process canceled; earlier effects may remain.')
            if overflow.is_set() or any(p.exists() and p.stat().st_size > limit for p, limit in watch_files):
                raise OutputLimitExceeded('Child process exceeded its output limit.')
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(args, timeout)
            if process.poll() is not None:
                break
            time.sleep(.02)
        if job is not None:
            win32job.TerminateJobObject(job, 1)
        elif os.name != 'nt':
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for thread in workers:
            thread.join()
        if overflow.is_set():
            raise OutputLimitExceeded('Child process exceeded its output limit.')
        return subprocess.CompletedProcess(args, process.returncode,
                                           captured[0].decode('utf-8', 'replace'),
                                           captured[1].decode('utf-8', 'replace'))
    finally:
        if job is not None and assigned:
            win32job.TerminateJobObject(job, 1)
            while win32job.QueryInformationJobObject(job, win32job.JobObjectBasicAccountingInformation)[
                    'ActiveProcesses']:
                time.sleep(.01)
            job.Close()
        elif job is not None:
            job.Close()
        if process.poll() is None:
            if os.name == 'nt':
                try:
                    subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                except (OSError, subprocess.TimeoutExpired):
                    pass
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.kill()
        process.wait()
        for thread in workers:
            thread.join()
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe and not pipe.closed:
                pipe.close()
