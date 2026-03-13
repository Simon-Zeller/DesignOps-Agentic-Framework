"""Token Engine Crew stub — writes minimum required output files for p09 testing."""
from __future__ import annotations

import json
from pathlib import Path

from daf.crews._stub import StubCrew


def create_token_engine_crew(output_dir: str) -> StubCrew:
    """Return a stub Token Engine Crew that writes minimum required outputs."""
    od = Path(output_dir)

    def _run() -> None:
        compiled = od / "tokens" / "compiled"
        compiled.mkdir(parents=True, exist_ok=True)
        (od / "tokens").mkdir(parents=True, exist_ok=True)

        for name in (
            "variables.css",
            "variables-light.css",
            "variables-dark.css",
            "variables-high-contrast.css",
            "variables.scss",
        ):
            (compiled / name).write_text("/* stub */")

        (compiled / "tokens.ts").write_text("// stub")
        (compiled / "tokens.json").write_text(json.dumps({"stub": True}))
        (od / "tokens" / "diff.json").write_text(json.dumps({"stub": True}))

    return StubCrew(name="token_engine", run_fn=_run)
