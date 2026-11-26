"""Crash-released per-user runtime lock: one core queue per runtime directory."""
import os
from pathlib import Path


class InstanceLock:
    def __init__(self, path: Path):
        self._file = path.open('a+b')
        try:
            self._file.seek(0, os.SEEK_END)
            if self._file.tell() == 0:
                self._file.write(b'\0')
                self._file.flush()
            self._file.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self._file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self._file.close()
            raise RuntimeError('CLYDEX Core is already running for this user.') from exc

    def close(self) -> None:
        if self._file.closed:
            return
        self._file.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        self._file.close()
