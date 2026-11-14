from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_static_output import check
from config import ContractError


class StaticOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_valid_site_keeps_nojekyll(self):
        (self.root / "index.html").write_text("<!doctype html><title>site</title>")
        (self.root / ".nojekyll").touch()
        check(self.root)

    def test_missing_or_empty_index_fails(self):
        with self.assertRaises(ContractError):
            check(self.root)
        (self.root / "index.html").touch()
        with self.assertRaises(ContractError):
            check(self.root)

    def test_file_and_directory_symlinks_fail(self):
        (self.root / "index.html").write_text("site")
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside)
            file_target = external / "external.txt"
            file_target.write_text("external fixture payload")
            directory_target = external / "directory"
            directory_target.mkdir()
            for target in [file_target, directory_target]:
                with self.subTest(directory=target.is_dir()):
                    link = self.root / "external"
                    link.symlink_to(target, target_is_directory=target.is_dir())
                    try:
                        with self.assertRaisesRegex(ContractError, "cannot include symlinks"):
                            check(self.root)
                    finally:
                        link.unlink()

    def test_git_metadata_fails(self):
        (self.root / "index.html").write_text("site")
        (self.root / ".git").mkdir()
        with self.assertRaises(ContractError):
            check(self.root)
