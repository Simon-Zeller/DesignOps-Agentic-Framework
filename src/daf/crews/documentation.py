"""Documentation Crew stub."""
from __future__ import annotations

import json
from pathlib import Path

from daf.crews._stub import StubCrew


def create_documentation_crew(output_dir: str) -> StubCrew:
    od = Path(output_dir)

    def _run() -> None:
        docs = od / "docs"
        decisions = docs / "decisions"
        decisions.mkdir(parents=True, exist_ok=True)

        (docs / "README.md").write_text("")
        (docs / "tokens.md").write_text("")
        (docs / "search-index.json").write_text(json.dumps({"stub": True}))
        (decisions / "generation-narrative.md").write_text("")
        (docs / "changelog.md").write_text("")

    return StubCrew(name="documentation", run_fn=_run)
