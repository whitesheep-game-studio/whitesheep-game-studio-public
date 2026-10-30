"""Require an actual Windows preset and nonzero export, including zero-exit engine errors."""

import argparse
import configparser
from pathlib import Path
import re
import subprocess


def export(root, output, engine="godot"):
    presets = configparser.ConfigParser(interpolation=None, strict=True)
    presets.read(root / "export_presets.cfg")
    selected = [section for section in presets.sections()
                if re.fullmatch(r"preset\.\d+", section)
                and presets[section].get("name") == '"Windows Desktop"'
                and presets[section].get("platform") == '"Windows Desktop"']
    if len(selected) != 1:
        raise ValueError("Exactly one Windows Desktop export preset is required")
    if presets[selected[0]].get("export_filter") != '"all_resources"':
        raise ValueError("Initial Windows profile requires all_resources export")
    output.mkdir(parents=True, exist_ok=True)
    (output / ".gdignore").touch()
    target = output / "game.exe"
    result = subprocess.run([engine, "--headless", "--path", str(root), "--export-debug",
                             "Windows Desktop", str(target)], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    print(result.stdout, end="", flush=True)
    if result.returncode or re.search(r"(?m)^\s*(?:SCRIPT ERROR:|ERROR:|FAIL:)", result.stdout):
        raise RuntimeError("Godot Windows export failed")
    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError("Godot export produced no executable")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export(args.root.resolve(), args.output.resolve())
