"""Record the real job status, never treating a skipped/failed job as success."""

import os
from pathlib import Path

directory = Path(os.environ["GITHUB_WORKSPACE"]) / "ci-results"
directory.mkdir(exist_ok=True)
text = (f"CI result: {os.environ['CI_RESULT']}\n\n"
        f"Source commit: {os.environ['GITHUB_SHA']}\n\n"
        f"Event: {os.environ['GITHUB_EVENT_NAME']}\n\n"
        "Translation checks validate structure, not translation approval.\n")
(directory / "summary.md").write_text(text, encoding="utf-8")
with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
    stream.write(text)
