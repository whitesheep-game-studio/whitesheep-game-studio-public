"""Read an explicit project contract without allowing duplicate keys or unsafe paths."""

import json
from pathlib import Path
import re

import yaml


class ContractError(ValueError):
    pass


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"Duplicate key: {key}")
        result[key] = value
    return result


class UniqueLoader(yaml.SafeLoader):
    pass


def yaml_mapping(loader, node):
    return unique_pairs(loader.construct_pairs(node, deep=True))


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, yaml_mapping)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)


def inside(root, relative):
    if not isinstance(relative, str) or not relative or "\n" in relative or "\r" in relative:
        raise ContractError("Expected a nonempty single-line relative path")
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ContractError(f"Path escapes project: {relative}")
    return path


def commands(value, name):
    if not isinstance(value, list) or not value:
        raise ContractError(f"{name} must contain at least one command")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ContractError(f"{name} contains an empty/non-string command")


def reason(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{name} requires an explicit reason")


def load(root, filename, stack=None):
    config = yaml.load(inside(root, filename).read_text(encoding="utf-8"), Loader=UniqueLoader)
    if not isinstance(config, dict) or config.get("version") != 1:
        raise ContractError("Project contract must be a mapping with version: 1")
    allowed = {"version", "stack", "directory", "kind", "build", "data", "i18n",
               "dependencies", "checks", "requirements", "output"}
    if set(config) - allowed:
        raise ContractError(f"Unknown project settings: {sorted(set(config) - allowed)}")
    kind = config.get("stack")
    if kind not in {"flutter", "godot", "web", "python"} or (stack and kind != stack):
        raise ContractError("Workflow and project stack must match")
    work = inside(root, config.get("directory", "."))
    if not work.is_dir():
        raise ContractError("Project directory does not exist")
    project_kind = config.get("kind")
    if project_kind not in {"application", "library", "tool"}:
        raise ContractError("kind must be application, library or tool")
    if kind in {"godot", "web"} and project_kind != "application":
        raise ContractError("Godot and web profiles require kind: application")
    if kind == "flutter" and project_kind not in {"application", "library"}:
        raise ContractError("Flutter projects must declare application or library")
    data = config.get("data", {})
    if "commands" in data:
        commands(data["commands"], "data.commands")
    else:
        reason(data.get("reason"), "No additional project data")
    i18n = config.get("i18n", {})
    if i18n.get("format") == "none":
        if project_kind == "application":
            raise ContractError("Application i18n resources are required; no silent opt-out")
        reason(i18n.get("reason"), "No user-facing translations")
    elif i18n.get("format") not in {"arb", "csv", "po", "json"}:
        raise ContractError("Declare i18n.format: arb, csv, po, json or justified none")
    deps = config.get("dependencies", {})
    if deps.get("format") == "none":
        if kind != "godot" and kind != "python":
            raise ContractError("Flutter/web projects must audit their lockfiles")
        reason(deps.get("reason"), "No external package dependencies")
        if kind == "python" and list(work.glob("*requirements*.txt")):
            raise ContractError("Requirements exist: audit them instead of declaring none")
        if kind == "godot" and (work / "addons").exists():
            raise ContractError("Godot addons require an explicit dependency audit profile")
    elif deps.get("format") not in {"pub", "npm", "requirements"}:
        raise ContractError("Unsupported dependency audit profile")
    else:
        files = deps.get("files")
        if not isinstance(files, list) or not files:
            raise ContractError("Dependency audit needs explicit lockfile paths")
        for name in files:
            if not inside(work, name).is_file():
                raise ContractError(f"Missing dependency lockfile: {name}")
    build = config.get("build")
    supported = {"flutter": {"android-debug", "none"}, "godot": {"windows-debug"},
                 "web": {"static"}, "python": {"none"}}
    if build not in supported[kind]:
        raise ContractError(f"Unsupported {kind} build profile: {build}")
    if kind == "flutter":
        if project_kind == "application" and build != "android-debug":
            raise ContractError("Flutter applications require a representative Android build")
        if build == "android-debug" and not (work / "android").is_dir():
            raise ContractError("Android build requested without an Android project")
        config["sdk"] = read_json(work / ".fvmrc").get("flutter", "")
        if not (work / "pubspec.lock").is_file():
            raise ContractError("Frozen Flutter install requires pubspec.lock")
    elif kind == "godot":
        config["sdk"] = (work / ".godot-version").read_text().strip()
        if config["sdk"] not in {"4.6.3", "4.7.2"}:
            raise ContractError("Verify the engine/export checksums before supporting a new Godot")
        if not (work / "project.godot").is_file():
            raise ContractError("Missing project.godot")
        if not (work / "export_presets.cfg").is_file():
            raise ContractError("Windows export requires committed export_presets.cfg")
        commands(config.get("checks"), "checks (existing Godot test command)")
    else:
        config["sdk"] = "26.13.0" if kind == "web" else "3.15.2"
        commands(config.get("checks"), "checks")
    if not re.fullmatch(r"\d+\.\d+\.\d+", config["sdk"]) and kind in {"flutter", "godot"}:
        raise ContractError("SDK must be pinned to an exact stable version")
    if kind == "web" and not (work / "package-lock.json").is_file():
        raise ContractError("Web npm ci requires package-lock.json")
    if kind == "web":
        output = inside(work, config.get("output", "docs"))
        if output == work or output.is_relative_to(work / ".git"):
            raise ContractError("Static build output must be a dedicated directory")
        config["output"] = output
    for name in config.get("requirements", []):
        if not inside(work, name).is_file():
            raise ContractError(f"Missing Python requirement file: {name}")
    config["work"] = work
    return config
