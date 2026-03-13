"""AI Semantic Layer Crew stub."""
from __future__ import annotations

import json
from pathlib import Path

from daf.crews._stub import StubCrew


def create_ai_semantic_layer_crew(output_dir: str) -> StubCrew:
    od = Path(output_dir)

    def _run() -> None:
        registry = od / "registry"
        registry.mkdir(parents=True, exist_ok=True)

        for name in ("components.json", "tokens.json", "composition-rules.json", "compliance-rules.json"):
            (registry / name).write_text(json.dumps({"stub": True}))

        (od / ".cursorrules").write_text("")
        (od / "copilot-instructions.md").write_text("")
        (od / "ai-context.json").write_text(json.dumps({"stub": True}))

    return StubCrew(name="ai_semantic_layer", run_fn=_run)
