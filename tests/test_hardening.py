from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from clydex.automation.tasks import CancellationToken
from clydex.core.application import CoreApplication
from clydex.core.config import RuntimePaths
from clydex.core.processes import OutputLimitExceeded, run_process
from tests.test_regression import engine_for_test


class HardeningTests(unittest.TestCase):
    def test_unfinished_native_work_keeps_instance_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = RuntimePaths(Path(folder))
            with patch('clydex.core.application.legacy_recognition_mode', return_value=None):
                core = CoreApplication(paths=paths, engine=engine_for_test())
                entered, release = threading.Event(), threading.Event()
                def native_work():
                    entered.set()
                    release.wait(10)
                core.submit(native_work)
                self.assertTrue(entered.wait(1))
                try:
                    self.assertFalse(core.close())
                    with self.assertRaises(RuntimeError):
                        CoreApplication(paths=paths, engine=engine_for_test())
                finally:
                    release.set()
                    self.assertTrue(core.wait_closed(3))
                replacement = CoreApplication(paths=paths, engine=engine_for_test())
                replacement.close()

    def test_child_output_flood_is_bounded(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(OutputLimitExceeded):
            run_process([sys.executable, '-c', 'import sys; sys.stdout.write("x"*2000000)'],
                        input='', cwd=folder, timeout=3, cancel=CancellationToken(), max_output_bytes=4096)

    def test_child_timeout_terminates_execution(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(subprocess.TimeoutExpired):
            run_process([sys.executable, '-c', 'import time; time.sleep(30)'],
                        input='', cwd=folder, timeout=.1, cancel=CancellationToken())

    def test_generated_answer_file_is_limited(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'answer.json'
            with self.assertRaises(OutputLimitExceeded):
                run_process([sys.executable, '-c',
                             'from pathlib import Path; import time; '
                             'Path("answer.json").write_text("x"*10000); time.sleep(10)'],
                            input='', cwd=folder, timeout=3, cancel=CancellationToken(),
                            watch_files=((output, 100),))
