"""One serial worker per application service, bounded pending work and cancellation."""
from concurrent.futures import Future
from dataclasses import dataclass, field
import queue
import threading
import time
from typing import Callable

from clydex.core.errors import Cancelled


class CancellationToken:
    def __init__(self, timeout: float | None = None):
        self._event = threading.Event()
        self.deadline = time.monotonic() + timeout if timeout is not None else None

    def set(self) -> None:
        self._event.set()

    def is_set(self) -> bool:
        return self._event.is_set() or (self.deadline is not None and time.monotonic() >= self.deadline)

    def check(self) -> None:
        if self.is_set():
            raise Cancelled('Task canceled or timed out.')


@dataclass
class TaskHandle:
    future: Future = field(default_factory=Future)
    token: CancellationToken = field(default_factory=CancellationToken)

    def cancel(self) -> None:
        self.token.set()


class SupervisedQueue:
    def __init__(self, capacity: int = 1):
        if type(capacity) is not int or capacity < 1:
            raise ValueError('Invalid task queue capacity.')
        self._queue: queue.Queue = queue.Queue(maxsize=capacity)
        self._lock = threading.Lock()
        self._closed = False
        self._active: TaskHandle | None = None
        self._generation = 0
        self._thread = threading.Thread(target=self._run, name='clydex-core', daemon=True)
        self._thread.start()

    def submit(self, work: Callable[[CancellationToken], object], *, only_if_idle: bool = False) -> TaskHandle:
        handle = TaskHandle()
        with self._lock:
            if self._closed:
                raise RuntimeError('Task queue is closed.')
            if only_if_idle and (self._active is not None or self._queue.unfinished_tasks):
                raise queue.Full
            self._queue.put_nowait((handle, work, self._generation))
        return handle

    @property
    def busy(self) -> bool:
        with self._lock:
            return self._active is not None or bool(self._queue.unfinished_tasks)

    def _run(self) -> None:
        while True:
            try:
                handle, work, generation = self._queue.get(timeout=.05)
            except queue.Empty:
                with self._lock:
                    if self._closed:
                        return
                continue
            with self._lock:
                self._active = handle
                if self._closed or generation != self._generation:
                    handle.cancel()
            try:
                handle.token.check()
                if handle.future.set_running_or_notify_cancel():
                    handle.future.set_result(work(handle.token))
            except Exception as exc:
                if not handle.future.done():
                    handle.future.set_exception(exc)
            finally:
                with self._lock:
                    self._active = None
                self._queue.task_done()

    def cancel_all(self) -> None:
        with self._lock:
            self._generation += 1
            if self._active:
                self._active.cancel()
            while True:
                try:
                    handle, _, _ = self._queue.get_nowait()
                except queue.Empty:
                    break
                handle.cancel()
                handle.future.cancel()
                self._queue.task_done()

    def close(self, timeout: float = 1) -> bool:
        with self._lock:
            self._closed = True
        self.cancel_all()
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout=timeout)
        return not self._thread.is_alive()

    def wait_closed(self) -> None:
        if threading.current_thread() is self._thread:
            raise RuntimeError('A worker cannot wait for its own shutdown.')
        self._thread.join()
