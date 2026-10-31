import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from config import ContractError, load


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = {"version": 1, "stack": "python", "kind": "tool", "directory": ".",
                       "build": "none", "checks": ["python -m unittest discover -s tests -v"],
                       "data": {"reason": "No product data in this tool"},
                       "i18n": {"format": "none", "reason": "CLI has no localized UI"},
                       "dependencies": {"format": "none", "reason": "Standard library only"}}

    def write(self, config=None):
        (self.root / "project.yml").write_text(yaml.safe_dump(config or self.config))

    def test_valid_python_tool(self):
        self.write()
        self.assertEqual(load(self.root, "project.yml", "python")["sdk"], "3.15.2")

    def test_contract_errors(self):
        mutations = [{"version": 2}, {"stack": "unity"}, {"directory": "../outside"},
                     {"directory": "/tmp"}, {"directory": "a\nb"}, {"unknown": 1},
                     {"checks": []}, {"checks": [""]}, {"data": {}},
                     {"kind": "application"}, {"dependencies": {"format": "none"}},
                     {"i18n": {"format": "none"}}, {"build": "fake-success"}]
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ContractError):
                self.write(self.config | mutation)
                load(self.root, "project.yml", "python")

    def test_duplicate_yaml_setting(self):
        (self.root / "project.yml").write_text('version: 1\nversion: 1\n')
        with self.assertRaises(ContractError):
            load(self.root, "project.yml")

    def test_stack_mismatch(self):
        self.write()
        with self.assertRaises(ContractError):
            load(self.root, "project.yml", "flutter")

    def test_symlink_escape(self):
        (self.root / "escape").symlink_to("/tmp", target_is_directory=True)
        self.write(self.config | {"directory": "escape"})
        with self.assertRaises(ContractError):
            load(self.root, "project.yml")

    def test_cannot_skip_existing_requirements(self):
        (self.root / "requirements.txt").write_text("PyYAML==6.0.3\n")
        self.write()
        with self.assertRaises(ContractError):
            load(self.root, "project.yml")

    def test_missing_audit_lockfile(self):
        self.write(self.config | {"dependencies": {"format": "requirements", "files": ["missing"]}})
        with self.assertRaises(ContractError):
            load(self.root, "project.yml")

    def test_web_output_cannot_escape_or_publish_entire_checkout(self):
        (self.root / "package-lock.json").write_text('{"lockfileVersion":3,"packages":{}}')
        config = self.config | {"stack": "web", "kind": "application", "build": "static",
                                "i18n": {"format": "json"},
                                "dependencies": {"format": "npm", "files": ["package-lock.json"]}}
        for output in ["..", ".", ".git", "/tmp", "docs\nother"]:
            with self.subTest(output=output), self.assertRaises(ContractError):
                self.write(config | {"output": output})
                load(self.root, "project.yml", "web")
        self.write(config | {"output": "docs"})
        self.assertEqual(load(self.root, "project.yml", "web")["output"], self.root / "docs")

    def test_flutter_requires_build_pin_and_lock(self):
        config = copy.deepcopy(self.config)
        config.update(stack="flutter", kind="library", build="none",
                      dependencies={"format": "pub", "files": ["pubspec.lock"]})
        (self.root / "pubspec.lock").write_text("packages: {}")
        (self.root / ".fvmrc").write_text(json.dumps({"flutter": "3.47.8"}))
        self.write(config)
        self.assertEqual(load(self.root, "project.yml")["sdk"], "3.47.8")
        (self.root / ".fvmrc").write_text(json.dumps({"flutter": "stable"}))
        with self.assertRaises(ContractError):
            load(self.root, "project.yml")

    def test_godot_accepts_verified_versions_and_rejects_unreviewed_engine(self):
        config = self.config | {"stack": "godot", "kind": "application",
                                "build": "windows-debug", "i18n": {"format": "csv"},
                                "dependencies": {"format": "none", "reason": "No addons"}}
        (self.root / "project.godot").touch()
        (self.root / "export_presets.cfg").touch()
        self.write(config)
        for version in ("4.6.3", "4.7.2"):
            (self.root / ".godot-version").write_text(version)
            self.assertEqual(load(self.root, "project.yml")["sdk"], version)
        (self.root / ".godot-version").write_text("4.8.0")
        with self.assertRaises(ContractError):
            load(self.root, "project.yml")

    def test_command_failure_preserves_exit_code(self):
        self.write(self.config | {"checks": ["exit 23"]})
        script = Path(__file__).resolve().parents[1] / "scripts/ci.py"
        result = subprocess.run([sys.executable, str(script), "checks", "--root", str(self.root),
                                 "--config", "project.yml", "--stack", "python"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 23)

    def test_invalid_resource_fails_actual_cli(self):
        self.write(self.config | {"i18n": {"format": "csv", "path": "absent.csv",
                                          "base": "en", "fallback": "en",
                                          "locales": ["ko", "ja", "en"]}})
        script = Path(__file__).resolve().parents[1] / "scripts/ci.py"
        result = subprocess.run([sys.executable, str(script), "i18n", "--root", str(self.root),
                                 "--config", "project.yml", "--stack", "python"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)

    def test_empty_unittest_suite_fails_actual_cli(self):
        (self.root / "tests").mkdir()
        self.write()
        script = Path(__file__).resolve().parents[1] / "scripts/ci.py"
        result = subprocess.run([sys.executable, str(script), "checks", "--root", str(self.root),
                                 "--config", "project.yml", "--stack", "python"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Ran 0 tests", result.stdout)

    def test_zero_test_report_with_success_exit_fails_actual_cli(self):
        self.write(self.config | {"checks": ["printf 'Ran 0 tests in 0.001s\\nOK\\n'"]})
        script = Path(__file__).resolve().parents[1] / "scripts/ci.py"
        result = subprocess.run([sys.executable, str(script), "checks", "--root", str(self.root),
                                 "--config", "project.yml", "--stack", "python"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("zero-test run", result.stderr)
