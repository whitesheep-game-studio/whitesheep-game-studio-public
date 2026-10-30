import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_dependencies import audit, packages
from config import ContractError


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = {"format": "requirements", "files": ["requirements.txt"]}
        (self.root / "requirements.txt").write_text("PyYAML==6.0.3\n")

    def test_clean_query(self):
        seen = []

        def request(batch):
            seen.extend(batch)
            return {"results": [{}]}

        audit(self.root, self.config, request)
        self.assertEqual(seen, [("PyPI", "PyYAML", "6.0.3")])

    def test_vulnerability_fails(self):
        with self.assertRaisesRegex(ContractError, "TEST-123"):
            audit(self.root, self.config, lambda _: {"results": [{"vulns": [{"id": "TEST-123"}]}]})

    def test_incomplete_api_response_fails(self):
        for result in [{}, {"results": []}, {"results": [{"error": "unavailable"}]}]:
            with self.subTest(result=result), self.assertRaises(ContractError):
                audit(self.root, self.config, lambda _: result)

    def test_network_failure_is_not_success(self):
        def unavailable(_):
            raise OSError("service unavailable")
        with self.assertRaises(OSError):
            audit(self.root, self.config, unavailable)

    def test_unpinned_requirements_and_empty_list_fail(self):
        for text in ["", "requests>=2", "-r other.txt", "package @ https://example.com"]:
            with self.subTest(text=text), self.assertRaises(ContractError):
                (self.root / "requirements.txt").write_text(text)
                packages(self.root, self.config)

    def test_npm_transitive_and_scoped_package(self):
        (self.root / "package-lock.json").write_text(json.dumps({"lockfileVersion": 3, "packages": {
            "": {"name": "app"}, "node_modules/foo": {"version": "1.2.3"},
            "node_modules/foo/node_modules/@scope/bar": {"version": "2.3.4"}}}))
        self.assertEqual(packages(self.root, {"format": "npm", "files": ["package-lock.json"]}),
                         [("npm", "@scope/bar", "2.3.4"), ("npm", "foo", "1.2.3")])

    def test_pub_hosted_and_immutable_git(self):
        (self.root / "pubspec.lock").write_text('''packages:
  example:
    source: hosted
    version: 1.2.3
    description:
      url: https://pub.dev
  studio:
    source: git
    version: 0.1.0
    description:
      resolved-ref: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
''')
        self.assertEqual(packages(self.root, {"format": "pub", "files": ["pubspec.lock"]}),
                         [("Pub", "example", "1.2.3")])

    def test_mutable_git_dependency_fails(self):
        (self.root / "pubspec.lock").write_text('''packages:
  studio:
    source: git
    version: 0.1.0
    description:
      resolved-ref: main
''')
        with self.assertRaises(ContractError):
            packages(self.root, {"format": "pub", "files": ["pubspec.lock"]})
