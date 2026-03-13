"""Release Crew stub."""
from __future__ import annotations

import json
from pathlib import Path

from daf.crews._stub import StubCrew


def create_release_crew(output_dir: str) -> StubCrew:
    od = Path(output_dir)

    def _run() -> None:
        (od / "package.json").write_text(json.dumps({"stub": True}))

        # Ensure reports/generation-summary.json has a final_status marker
        reports = od / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        summary_path = reports / "generation-summary.json"
        if summary_path.exists():
            try:
                data = json.loads(summary_path.read_text())
            except (json.JSONDecodeError, OSError):
                data = {"stub": True}
            data["final_status"] = "stub"
            summary_path.write_text(json.dumps(data))
        else:
            summary_path.write_text(json.dumps({"stub": True, "final_status": "stub"}))

        # docs/changelog.md (if not already written by documentation crew)
        docs = od / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        changelog = docs / "changelog.md"
        if not changelog.exists():
            changelog.write_text("")

    return StubCrew(name="release", run_fn=_run)
