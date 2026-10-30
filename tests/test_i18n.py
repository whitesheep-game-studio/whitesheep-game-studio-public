import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_i18n import check, icu_arguments, named_arguments
from config import ContractError


class I18nTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = {"format": "arb", "locales": ["ko", "ja", "en"],
                       "base": "en", "fallback": "en", "directory": ".",
                       "files": {locale: f"{locale}.arb" for locale in ["ko", "ja", "en"]}}
        for locale in self.config["locales"]:
            self.write(locale, {"@@locale": locale, "welcome": "Hello {name}",
                                "@welcome": {"placeholders": {"name": {"type": "String"}}}})

    def write(self, locale, value):
        (self.root / f"{locale}.arb").write_text(json.dumps(value), encoding="utf-8")

    def test_valid_arb(self):
        check(self.root, self.config)

    def test_nested_plural_and_select(self):
        self.assertEqual(icu_arguments("{count, plural, =0{None} other{Hello {name}: "
                                       "{gender, select, male{his} other{their}} #}}"),
                         {"count", "name", "gender"})

    def test_invalid_icu(self):
        for text in ["{name", "hi}", "{0}", "{x, plural, one{One}}",
                     "{x, plural, other{a} other{b}}", "{x, date}",
                     "{x, select, offset:1 other{a}}", "{x, plural, typo{x} other{y}}",
                     "'{name}'"]:
            with self.subTest(text=text), self.assertRaises(ContractError):
                icu_arguments(text)

    def test_missing_translation_key(self):
        self.write("ja", {"@@locale": "ja"})
        with self.assertRaises(ContractError):
            check(self.root, self.config)

    def test_duplicate_json_key(self):
        (self.root / "ko.arb").write_text('{"@@locale":"ko","x":"a","x":"b"}')
        with self.assertRaises(ContractError):
            check(self.root, self.config)

    def test_placeholder_mismatch(self):
        self.write("ja", {"@@locale": "ja", "welcome": "Hello {other}",
                          "@welcome": {"placeholders": {"other": {}}}})
        with self.assertRaises(ContractError):
            check(self.root, self.config)

    def test_missing_metadata(self):
        self.write("ja", {"@@locale": "ja", "welcome": "Hello {name}"})
        with self.assertRaises(ContractError):
            check(self.root, self.config)

    def test_wrong_locale(self):
        self.write("ja", {"@@locale": "fr", "welcome": "Bonjour"})
        with self.assertRaises(ContractError):
            check(self.root, self.config)

    def test_extra_locale_resource(self):
        self.write("fr", {"@@locale": "fr"})
        with self.assertRaises(ContractError):
            check(self.root, self.config)

    def test_invalid_json(self):
        (self.root / "ko.arb").write_text('{"incomplete":')
        with self.assertRaises(ValueError):
            check(self.root, self.config)

    def test_zero_translations(self):
        for locale in self.config["locales"]:
            self.write(locale, {"@@locale": locale})
        with self.assertRaises(ContractError):
            check(self.root, self.config)

    def csv_config(self, text):
        (self.root / "strings.csv").write_text(text, encoding="utf-8")
        return {"format": "csv", "path": "strings.csv", "locales": ["ko", "ja", "en"],
                "base": "en", "fallback": "en"}

    def test_valid_godot_csv(self):
        check(self.root, self.csv_config('keys,ko,ja,en\nhello,안녕 {name},こんにちは {name},Hi {name}\n'))

    def test_csv_errors(self):
        for text in ['keys,ko,ja,en\nx,a,b,c\nx,a,b,c\n',
                     'keys,ko,ja,en\nx,,b,c\n', 'keys,ko,ja,en,fr\nx,a,b,c,d\n',
                     'keys,ko,ja,en\nx,a,b\n', 'keys,ko,ja,en\nx,{count},{name},{name}\n']:
            with self.subTest(text=text), self.assertRaises(ContractError):
                check(self.root, self.csv_config(text))

    def test_named_placeholder_rejects_positional_and_syntax(self):
        for text in ['Hi %s', '{0}', '{name', '{count, plural, other{#}}']:
            with self.subTest(text=text), self.assertRaises(ContractError):
                named_arguments(text)

    def test_web_json_export_contract(self):
        config = self.config | {"format": "json", "files": {locale: f"{locale}.json"
                                                             for locale in ["ko", "ja", "en"]}}
        for locale in config["locales"]:
            (self.root / f"{locale}.json").write_text('{"hello": "Hi {name}"}')
        check(self.root, config)

    def test_po_catalog_and_invalid_plural(self):
        import polib
        config = self.config | {"format": "po", "files": {locale: f"{locale}.po"
                                                           for locale in ["ko", "ja", "en"]}}
        for locale in config["locales"]:
            catalog = polib.POFile()
            catalog.metadata = {"Language": locale}
            catalog.append(polib.POEntry(msgid="HELLO", msgstr="Hi {name}"))
            catalog.save(str(self.root / f"{locale}.po"))
        check(self.root, config)
        catalog[0].flags.append("fuzzy")
        catalog.save(str(self.root / "en.po"))
        with self.assertRaises(ContractError):
            check(self.root, config)
