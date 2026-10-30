import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from export_godot import export
from prepare_release import prepare


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_release_checksum_and_repeatability(self):
        (self.root / "app.apk").write_bytes(b"real fixture payload")
        prepare(self.root, "v1.2.3")
        expected = hashlib.sha256(b"real fixture payload").hexdigest() + "  app.apk\n"
        self.assertEqual((self.root / "SHA256SUMS").read_text(), expected)
        prepare(self.root, "v1.2.3")
        self.assertEqual((self.root / "SHA256SUMS").read_text(), expected)

    def test_release_rejects_empty_directory_and_invalid_tag(self):
        for tag in ["v1.2.3", "main", "v1.2", "v1.2.3\n"]:
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                prepare(self.root, tag)

    def test_release_rejects_external_symlink(self):
        (self.root / "linked").symlink_to("/etc/hosts")
        with self.assertRaises(ValueError):
            prepare(self.root, "v1.2.3")

    def preset(self):
        (self.root / "export_presets.cfg").write_text('''[preset.0]
name="Windows Desktop"
platform="Windows Desktop"
export_filter="all_resources"
''')

    def test_export_rejects_absent_preset(self):
        with self.assertRaises(ValueError):
            export(self.root, self.root / "output")

    @patch("export_godot.subprocess.run")
    def test_engine_error_with_zero_exit_fails(self, run):
        self.preset()
        run.return_value = subprocess.CompletedProcess([], 0, stdout="ERROR: invalid resource\n")
        with self.assertRaises(RuntimeError):
            export(self.root, self.root / "output")

    @patch("export_godot.subprocess.run")
    def test_export_without_output_fails(self, run):
        self.preset()
        run.return_value = subprocess.CompletedProcess([], 0, stdout="Export complete\n")
        with self.assertRaises(RuntimeError):
            export(self.root, self.root / "output")
