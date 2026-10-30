from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from config import ContractError
from validate_workflows import validate


class WorkflowTests(unittest.TestCase):
    def test_shipped_workflow_policy(self):
        validate(Path(__file__).resolve().parents[1])

    def test_mutable_action_is_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            workflows = root / ".github/workflows"
            workflows.mkdir(parents=True)
            content = '''permissions:
  contents: read
jobs:
  check:
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@main
'''
            for index in range(5):
                (workflows / f"test-{index}.yml").write_text(content)
            with self.assertRaisesRegex(ContractError, "full SHA"):
                validate(root)
