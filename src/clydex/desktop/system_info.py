"""Local sampled OS counters. Unavailable/first CPU sample stays null."""
import os
import platform
import time


class SystemInformation:
    def __init__(self):
        self._previous = None
        self._updated = 0.
        self._snapshot = dict(os=platform.system(), release=platform.release(), cpu_percent=None,
                              memory_percent=None, memory_total_bytes=None, process_memory_bytes=None)

    def sample(self) -> dict:
        if time.monotonic() - self._updated < 1:
            return dict(self._snapshot)
        self._updated = time.monotonic()
        if os.name != 'nt':
            return dict(self._snapshot)
        import ctypes
        from ctypes import wintypes
        class MemoryStatus(ctypes.Structure):
            _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD)] + [
                (name, ctypes.c_ulonglong) for name in ('total', 'available', 'page_total', 'page_available',
                                                       'virtual_total', 'virtual_available', 'extended')]
        class ProcessMemory(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ('peak', 'working', 'pool_peak', 'pool', 'nonpool_peak',
                                                   'nonpool', 'page', 'page_peak')]
        try:
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            memory = MemoryStatus()
            memory.length = ctypes.sizeof(memory)
            if kernel.GlobalMemoryStatusEx(ctypes.byref(memory)):
                self._snapshot.update(memory_percent=memory.load, memory_total_bytes=memory.total)
            idle, system, user = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
            if kernel.GetSystemTimes(ctypes.byref(idle), ctypes.byref(system), ctypes.byref(user)):
                numbers = tuple(x.dwLowDateTime + (x.dwHighDateTime << 32) for x in (idle, system, user))
                if self._previous:
                    delta = sum(numbers[1:]) - sum(self._previous[1:])
                    if delta > 0:
                        self._snapshot['cpu_percent'] = round(max(0, min(100,
                            100 * (1 - (numbers[0] - self._previous[0]) / delta))), 1)
                self._previous = numbers
            counters = ProcessMemory()
            counters.cb = ctypes.sizeof(counters)
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            psapi = ctypes.WinDLL('psapi', use_last_error=True)
            psapi.GetProcessMemoryInfo.argtypes = (wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD)
            if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
                self._snapshot['process_memory_bytes'] = counters.working
        except (OSError, AttributeError):
            pass
        return dict(self._snapshot)
