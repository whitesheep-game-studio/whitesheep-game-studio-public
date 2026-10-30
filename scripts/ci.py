"""Execute project checks and preserve the original failure status."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

from config import ContractError, load
from check_i18n import check as check_i18n
from audit_dependencies import audit


def run(command, work):
    print(f"+ {command}", flush=True)
    result = subprocess.run(["bash", "-euo", "pipefail", "-c", command], cwd=work,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout, end="", flush=True)
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command)
    if re.search(r"(?im)^\s*(?:Ran 0 tests\b|no tests ran\b|No tests were found\b)", result.stdout):
        raise ContractError("A zero-test run is not a successful verification")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["preflight", "data", "i18n", "audit", "checks"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--config", default=".ci/project.yml")
    parser.add_argument("--stack", required=True)
    args = parser.parse_args()
    config = load(args.root.resolve(), args.config, args.stack)
    work = config["work"]
    if args.phase == "preflight":
        if output := os.environ.get("GITHUB_OUTPUT"):
            with open(output, "a", encoding="utf-8") as stream:
                stream.write(f"sdk={config['sdk']}\nwork={work}\nbuild={config['build']}\n")
                if args.stack == "web":
                    stream.write(f"site-output={config['output']}\n")
        print(f"Valid {args.stack} contract at {work}")
    elif args.phase == "data":
        if "commands" in config["data"]:
            for command in config["data"]["commands"]:
                run(command, work)
        else:
            print("No additional project data:", config["data"]["reason"])
    elif args.phase == "i18n":
        check_i18n(work, config["i18n"])
    elif args.phase == "audit":
        audit(work, config["dependencies"])
    elif args.phase == "checks":
        for command in config["checks"]:
            run(command, work)


if __name__ == "__main__":
    try:
        main()
    except (ContractError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"CI failed: {error}", file=sys.stderr)
        sys.exit(error.returncode if isinstance(error, subprocess.CalledProcessError) else 1)
