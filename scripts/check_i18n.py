"""Validate resource structure. Translation wording is owned by each product/WSDS."""

import csv
from io import StringIO
import re

import polib

from config import ContractError, inside, read_json


def icu_arguments(message):
    """Parse the named/simple, plural/select/selectordinal ICU subset used by Flutter.

    Unsupported ICU number/date skeletons and apostrophe escaping fail explicitly;
    do not guess their placeholder semantics. Products needing these extend fixtures first.
    """
    if not isinstance(message, str) or not message.strip():
        raise ContractError("Translation must be a nonempty string")
    names = set()
    index = 0

    def spaces():
        nonlocal index
        while index < len(message) and message[index].isspace():
            index += 1

    def token(pattern):
        nonlocal index
        spaces()
        match = re.match(pattern, message[index:])
        if not match:
            raise ContractError(f"Malformed ICU argument at offset {index}: {message}")
        index += len(match[0])
        return match[0]

    def body(nested=False):
        nonlocal index
        while index < len(message):
            char = message[index]
            if char == "}":
                if not nested:
                    raise ContractError("Unmatched closing brace")
                index += 1
                return
            if char == "'" and index + 1 < len(message) and message[index + 1] in "{}'":
                raise ContractError("ICU apostrophe escaping requires an explicit adapter")
            if char != "{":
                index += 1
                continue
            index += 1
            name = token(r"[A-Za-z_][A-Za-z0-9_]*")
            names.add(name)
            spaces()
            if index < len(message) and message[index] == "}":
                index += 1
                continue
            token(r",")
            argument_type = token(r"[a-z]+")
            if argument_type not in {"plural", "select", "selectordinal"}:
                raise ContractError(f"Unsupported ICU argument type: {argument_type}")
            token(r",")
            spaces()
            if message[index:].startswith("offset:"):
                if argument_type == "select":
                    raise ContractError("select cannot have an offset")
                token(r"offset:\s*\d+")
            options = set()
            while True:
                spaces()
                if index >= len(message):
                    raise ContractError("Unclosed ICU argument")
                if message[index] == "}":
                    index += 1
                    break
                option = token(r"(?:=\d+|[A-Za-z][A-Za-z0-9_]*)")
                if option in options:
                    raise ContractError("Duplicate ICU option")
                if argument_type != "select" and not re.fullmatch(
                    r"(?:=\d+|zero|one|two|few|many|other)", option
                ):
                    raise ContractError("Invalid plural option")
                options.add(option)
                token(r"\{")
                body(True)
            if "other" not in options:
                raise ContractError("ICU plural/select requires other")
        if nested:
            raise ContractError("Unclosed ICU body")

    body()
    return names


def named_arguments(message):
    if not isinstance(message, str) or not message.strip():
        raise ContractError("Translation must be nonempty")
    names = set(re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", message))
    remainder = re.sub(r"\{[A-Za-z_][A-Za-z0-9_]*\}", "", message)
    if "{" in remainder or "}" in remainder or re.search(r"%(?:\d+\$)?[sdf]", message):
        raise ContractError("Use matching named {placeholders}; positional/ICU syntax unsupported")
    return names


def check(root, config):
    fmt = config.get("format")
    if fmt == "none":
        print("i18n not applicable:", config["reason"])
        return
    locales = config.get("locales")
    if not isinstance(locales, list) or len(locales) != 3 or set(locales) != {"ko", "ja", "en"}:
        raise ContractError("Supported locales must be exactly ko, ja, en without duplicates")
    if config.get("base") not in locales or config.get("fallback") not in locales:
        raise ContractError("Declare existing base and fallback locales")
    resources = {}
    if fmt == "csv":
        rows = csv.reader(StringIO(inside(root, config["path"]).read_text(encoding="utf-8-sig")),
                          strict=True)
        header = next(rows, [])
        if len(header) != len(set(header)) or set(header) != {"keys", *locales}:
            raise ContractError("Godot CSV requires keys and exactly the supported locale columns")
        resources = {locale: {} for locale in locales}
        for row in rows:
            if len(row) != len(header):
                raise ContractError("CSV row has wrong number of columns")
            values = dict(zip(header, row))
            key = values["keys"]
            for locale in locales:
                if key in resources[locale]:
                    raise ContractError(f"Duplicate translation key: {key}")
                resources[locale][key] = values[locale]
    elif fmt in {"arb", "json", "po"}:
        directory = inside(root, config["directory"])
        pattern = config.get("pattern", "*." + fmt)
        if "/" in pattern or "\\" in pattern:
            raise ContractError("i18n.pattern must be a filename glob")
        files = sorted(directory.glob(pattern))
        declared = config.get("files", {})
        if set(declared) != set(locales):
            raise ContractError("Map each supported locale to exactly one resource filename")
        if {file.name for file in files} != set(declared.values()):
            raise ContractError("Missing or unexpected locale resource file")
        for locale, name in declared.items():
            path = inside(directory, name)
            if fmt == "po":
                catalog = polib.pofile(str(path), check_for_duplicates=True)
                if catalog.metadata.get("Language") != locale:
                    raise ContractError("PO Language does not match declared locale")
                values = {}
                for entry in catalog:
                    if entry.obsolete:
                        continue
                    if entry.fuzzy or entry.msgid_plural or entry.msgctxt:
                        raise ContractError("Fuzzy, contextual or plural PO needs a dedicated adapter")
                    values[entry.msgid] = entry.msgstr
                resources[locale] = values
            else:
                data = read_json(path)
                if not isinstance(data, dict):
                    raise ContractError("Locale resource must be an object")
                if fmt == "arb" and data.get("@@locale") != locale:
                    raise ContractError("ARB @@locale does not match declared locale")
                values = {key: value for key, value in data.items() if not key.startswith("@")}
                if fmt == "arb":
                    for key, metadata in data.items():
                        if key.startswith("@") and not key.startswith("@@") and key[1:] not in values:
                            raise ContractError("Orphan ARB metadata")
                    for key, value in values.items():
                        declared_args = data.get("@" + key, {}).get("placeholders", {})
                        if not isinstance(declared_args, dict):
                            raise ContractError("ARB placeholders must be an object")
                        if set(declared_args) != icu_arguments(value):
                            raise ContractError(f"ARB placeholder metadata mismatch: {key}")
                resources[locale] = values
    else:
        raise ContractError("Unsupported localization format")
    base = resources[config["base"]]
    if not base:
        raise ContractError("Base language contains zero translations")
    parse = icu_arguments if fmt == "arb" else named_arguments
    for key in base:
        if not isinstance(key, str) or not key.strip() or any(char.isspace() for char in key):
            raise ContractError("Translation keys must be nonempty without whitespace")
    for locale, values in resources.items():
        if values.keys() != base.keys():
            raise ContractError(f"Translation key set differs: {locale}")
        for key, text in values.items():
            if parse(text) != parse(base[key]):
                raise ContractError(f"Placeholder mismatch: {locale}/{key}")
    print(f"i18n structure valid: {len(base)} keys across {', '.join(locales)}")
