import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ReportingTests(unittest.TestCase):
    def test_failure_status_is_recorded_as_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            summary = root / "summary.md"
            script = Path(__file__).resolve().parents[1] / "scripts/record_result.py"
            environment = os.environ | {"GITHUB_WORKSPACE": str(root),
                                         "GITHUB_STEP_SUMMARY": str(summary),
                                         "CI_RESULT": "failure", "GITHUB_SHA": "a" * 40,
                                         "GITHUB_EVENT_NAME": "pull_request"}
            subprocess.run([sys.executable, str(script)], env=environment, check=True)
            text = summary.read_text()
            self.assertIn("CI result: failure", text)
            self.assertEqual((root / "ci-results/summary.md").read_text(), text)
