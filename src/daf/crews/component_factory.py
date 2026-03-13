"""Component Factory Crew stub."""
from __future__ import annotations

import json
from pathlib import Path

from daf.crews._stub import StubCrew


def create_component_factory_crew(output_dir: str) -> StubCrew:
    od = Path(output_dir)

    def _run() -> None:
        reports = od / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "quality-scorecard.json").write_text(json.dumps({"stub": True}))
        (reports / "a11y-audit.json").write_text(json.dumps({"stub": True}))
        (reports / "composition-audit.json").write_text(json.dumps({"stub": True}))

    return StubCrew(name="component_factory", run_fn=_run)
