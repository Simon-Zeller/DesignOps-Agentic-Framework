"""Governance Crew stub."""
from __future__ import annotations

import json
from pathlib import Path

from daf.crews._stub import StubCrew


def create_governance_crew(output_dir: str) -> StubCrew:
    od = Path(output_dir)

    def _run() -> None:
        governance = od / "governance"
        governance.mkdir(parents=True, exist_ok=True)
        templates = od / "docs" / "templates"
        templates.mkdir(parents=True, exist_ok=True)
        tests_dir = od / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        for name in ("ownership.json", "quality-gates.json", "deprecation-policy.json", "workflow.json"):
            (governance / name).write_text(json.dumps({"stub": True}))

        (templates / "rfc-template.md").write_text("")

        for name in ("tokens.test.ts", "a11y.test.ts", "composition.test.ts", "compliance.test.ts"):
            (tests_dir / name).write_text("// stub")

    return StubCrew(name="governance", run_fn=_run)
