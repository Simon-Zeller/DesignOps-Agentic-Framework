"""Analytics Crew stub."""
from __future__ import annotations

import json
from pathlib import Path

from daf.crews._stub import StubCrew


def create_analytics_crew(output_dir: str) -> StubCrew:
    od = Path(output_dir)

    def _run() -> None:
        reports = od / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "token-compliance.json").write_text(json.dumps({"stub": True}))
        (reports / "drift-report.json").write_text(json.dumps({"stub": True}))

    return StubCrew(name="analytics", run_fn=_run)
