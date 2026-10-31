"""Reject absent/empty static output and symlinks before transferring a site artifact."""

import argparse
from pathlib import Path

from config import ContractError


def check(directory):
    if not directory.is_dir() or directory.is_symlink():
        raise ContractError("Static output must be an existing regular directory")
    index = directory / "index.html"
    if not index.is_file() or index.stat().st_size == 0:
        raise ContractError("Static output requires a nonempty index.html")
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ContractError("Static artifacts cannot include symlinks")
        if path.name == ".git":
            raise ContractError("Static artifacts cannot include Git metadata")
    print("Static output verified:", directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    check(args.directory)
