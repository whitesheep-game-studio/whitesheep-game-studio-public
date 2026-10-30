"""Prepare local release metadata; never publish a Release or upload to a store."""

import argparse
import hashlib
from pathlib import Path
import re


def prepare(directory, tag):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("Release tag must be vMAJOR.MINOR.PATCH")
    files = sorted(path for path in directory.rglob("*") if path.is_file()
                   and path.name not in {"SHA256SUMS", "RELEASE_NOTES.md"})
    if not files:
        raise ValueError("Cannot prepare a release without build artifacts")
    lines = []
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError("Release inputs must be regular files inside the artifact directory")
        name = path.relative_to(directory).as_posix()
        if any(char in name for char in "\n\r\\"):
            raise ValueError("Unsafe artifact filename")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        lines.append(f"{digest}  {name}")
    (directory / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    (directory / "RELEASE_NOTES.md").write_text(
        f"# {tag}\n\nPrepared artifacts and SHA-256 checksums.\n\n"
        "Review platform coverage, signing and product notes before publication.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    prepare(args.directory, args.tag)
