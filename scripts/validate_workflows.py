"""Enforce immutable actions, explicit permissions and starter metadata."""

import json
from pathlib import Path
import re

import yaml

from config import ContractError, UniqueLoader


def validate(root):
    workflows = sorted((root / ".github/workflows").glob("*.yml"))
    if len(workflows) < 5:
        raise ContractError("Expected four reusable profiles and their validation workflow")
    for path in workflows:
        workflow = yaml.load(path.read_text(), Loader=UniqueLoader)
        if workflow.get("permissions") != {"contents": "read"}:
            raise ContractError(f"Read-only contents permissions required: {path}")
        for job in workflow["jobs"].values():
            if "timeout-minutes" not in job:
                raise ContractError(f"Set a job timeout: {path}")
            for step in job.get("steps", []):
                reference = step.get("uses")
                if reference and not re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", reference):
                    raise ContractError(f"Action must use a full SHA: {reference}")
                if step.get("continue-on-error"):
                    raise ContractError("Do not mask required step failures")
        if path.name.startswith("reusable-"):
            event = workflow.get("on", workflow.get(True, {}))
            if "workflow_call" not in event:
                raise ContractError("Reusable workflow requires workflow_call")
    for stack in ["flutter", "godot", "web", "python"]:
        template = root / "workflow-templates" / f"{stack}-ci.yml"
        metadata = template.with_suffix(".properties.json")
        data = json.loads(metadata.read_text())
        if not data.get("name") or not data.get("description") or not data.get("categories"):
            raise ContractError(f"Invalid workflow template metadata: {metadata}")
        content = template.read_text()
        if f"reusable-{stack}.yml@REPLACE_WITH_TESTED_HUB_SHA" not in content:
            raise ContractError("Starter must explicitly require a tested hub revision")
        if "secrets: inherit" in content:
            raise ContractError("Do not inherit all caller secrets")
    print(f"Workflow policy valid: {len(workflows)} workflows, 4 starter pairs")


if __name__ == "__main__":
    validate(Path(__file__).resolve().parents[1])
