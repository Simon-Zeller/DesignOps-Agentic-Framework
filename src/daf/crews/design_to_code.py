"""Design-to-Code Crew stub."""
from __future__ import annotations

import json
from pathlib import Path

from daf.crews._stub import StubCrew


def create_design_to_code_crew(output_dir: str) -> StubCrew:
    od = Path(output_dir)

    def _run() -> None:
        (od / "src" / "primitives").mkdir(parents=True, exist_ok=True)
        (od / "src" / "components").mkdir(parents=True, exist_ok=True)
        (od / "reports").mkdir(parents=True, exist_ok=True)
        (od / "screenshots").mkdir(parents=True, exist_ok=True)

        (od / "src" / "primitives" / "index.ts").write_text("// stub")
        (od / "src" / "components" / "index.ts").write_text("// stub")
        (od / "src" / "index.ts").write_text("// stub")
        (od / "reports" / "generation-summary.json").write_text(json.dumps({"stub": True}))

    return StubCrew(name="design_to_code", run_fn=_run)
