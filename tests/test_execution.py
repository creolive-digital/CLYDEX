from concurrent.futures import CancelledError
import queue
import sys
import tempfile
import threading
import time
import unittest

from clydex.automation.tasks import CancellationToken, SupervisedQueue
from clydex.core.errors import Cancelled
from clydex.core.processes import run_process


class ExecutionTests(unittest.TestCase):
    def test_serial_order_and_bounded_queue(self):
        tasks = SupervisedQueue(1)
        self.addCleanup(tasks.close)
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        order = []
        def first(token):
            entered.set()
            release.wait(2)
            order.append(1)
        a = tasks.submit(first)
        self.assertTrue(entered.wait(2))
        b = tasks.submit(lambda token: order.append(2))
        with self.assertRaises(queue.Full):
            tasks.submit(lambda token: None)
        release.set()
        a.future.result(2)
        b.future.result(2)
        self.assertEqual(order, [1, 2])

    def test_stop_cancels_current_and_pending_tasks(self):
        tasks = SupervisedQueue(1)
        self.addCleanup(tasks.close)
        entered = threading.Event()
        def active(token):
            entered.set()
            while not token.is_set():
                time.sleep(.005)
            token.check()
        a = tasks.submit(active)
        self.assertTrue(entered.wait(2))
        effects = []
        b = tasks.submit(lambda token: effects.append('bad'))
        tasks.cancel_all()
        with self.assertRaises(Cancelled):
            a.future.result(2)
        with self.assertRaises(CancelledError):
            b.future.result(2)
        self.assertEqual(effects, [])
        self.assertEqual(tasks.submit(lambda token: 'new request').future.result(2), 'new request')

    def test_failure_does_not_kill_worker_and_close_denies_work(self):
        tasks = SupervisedQueue()
        def fail(token):
            raise ValueError('failure')
        with self.assertRaises(ValueError):
            tasks.submit(fail).future.result(2)
        self.assertEqual(tasks.submit(lambda token: 42).future.result(2), 42)
        tasks.close()
        with self.assertRaises(RuntimeError):
            tasks.submit(lambda token: None)

    def test_deadline_cancels_before_execution(self):
        token = CancellationToken(timeout=0)
        with self.assertRaises(Cancelled):
            token.check()

    def test_process_input_is_literal_and_output_retained(self):
        with tempfile.TemporaryDirectory() as folder:
            result = run_process([sys.executable, '-c', 'import sys; print(sys.stdin.read())'],
                                 input='literal $() & ; text', cwd=folder, timeout=5,
                                 cancel=CancellationToken())
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'literal $() & ; text')

    def test_running_process_cancelled(self):
        token = CancellationToken()
        timer = threading.Timer(.15, token.set)
        timer.start()
        self.addCleanup(timer.cancel)
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(Cancelled):
            run_process([sys.executable, '-c', 'import time; time.sleep(30)'],
                        input='', cwd=folder, timeout=5, cancel=token)
