"""Audit resolved dependency versions against OSV; network/API failures fail CI."""

import json
import re
import urllib.request

import yaml

from config import ContractError, UniqueLoader, inside, read_json


def packages(root, config):
    found = set()
    for filename in config["files"]:
        path = inside(root, filename)
        if config["format"] == "pub":
            lock = yaml.load(path.read_text(), Loader=UniqueLoader)
            for name, item in lock["packages"].items():
                if item["source"] == "hosted":
                    if item["description"].get("url") != "https://pub.dev":
                        raise ContractError("Private pub registries need an explicit audit adapter")
                    found.add(("Pub", name, item["version"]))
                elif item["source"] == "git":
                    # Git packages must be reviewed at immutable commits separately.
                    ref = item["description"].get("resolved-ref", "")
                    if not re.fullmatch(r"[0-9a-f]{40}", ref):
                        raise ContractError("Git dependency must be locked to a complete commit SHA")
                    print(f"Git dependency {name}@{ref}: no Pub advisory coverage")
                elif item["source"] != "sdk":
                    raise ContractError(f"Unreviewed Pub dependency source: {item['source']}")
        elif config["format"] == "npm":
            lock = read_json(path)
            if lock.get("lockfileVersion") not in {2, 3}:
                raise ContractError("Use npm lockfile version 2 or 3")
            for location, item in lock["packages"].items():
                if not location:
                    continue
                name = item.get("name") or location.rsplit("node_modules/", 1)[-1]
                version = item.get("version", "")
                if item.get("link") or not re.match(r"^\d+\.\d+\.\d+", version):
                    raise ContractError("Local/unversioned npm packages require an audit adapter")
                found.add(("npm", name, version))
        elif config["format"] == "requirements":
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)", line)
                if not match:
                    raise ContractError("Audit requirements must be flattened exact name==version pins")
                found.add(("PyPI", *match.groups()))
    if not found:
        raise ContractError("Dependency lockfiles produced zero auditable package versions")
    return sorted(found)


def query(batch):
    payload = {"queries": [{"package": {"ecosystem": ecosystem, "name": name}, "version": version}
                           for ecosystem, name, version in batch]}
    request = urllib.request.Request("https://api.osv.dev/v1/querybatch",
                                     data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def audit(root, config, request=query):
    if config["format"] == "none":
        print("Package advisory audit not applicable:", config["reason"])
        return
    items = packages(root, config)
    findings = []
    for start in range(0, len(items), 100):
        batch = items[start:start + 100]
        result = request(batch)
        results = result.get("results")
        if not isinstance(results, list) or len(results) != len(batch):
            raise ContractError("OSV returned an incomplete result")
        for package, match in zip(batch, results):
            if not isinstance(match, dict) or match.get("error"):
                raise ContractError("OSV returned an invalid result")
            for vulnerability in match.get("vulns", []):
                findings.append(f"{package}: {vulnerability['id']}")
    if findings:
        raise ContractError("Dependency advisories found:\n" + "\n".join(findings))
    print(f"No OSV advisories for {len(items)} resolved registry packages (point-in-time result)")
