"""Token Engine Crew — sequences Agents 7–11 to ingest, validate, compile,
check integrity, and diff design tokens.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from daf.crews._stub import StubCrew
from daf.agents.token_ingestion import _ingest_tokens
from daf.agents.token_validation import _validate_tokens
from daf.agents.token_compilation import _compile_tokens
from daf.agents.token_integrity import _check_integrity
from daf.agents.token_diff import _run_diff


def create_token_engine_crew(
    output_dir: str,
    brand_profile: dict[str, Any] | None = None,
) -> StubCrew:
    """Return a Token Engine Crew that runs Agents 7–11 sequentially.

    Args:
        output_dir: Root directory for all token I/O.
        brand_profile: Brand configuration dict with themes, archetype, etc.
            Defaults to a minimal single-theme profile if not provided.

    The crew raises RuntimeError if token validation produces any fatal
    violations, preventing compilation from running on invalid tokens.
    """
    if brand_profile is None:
        brand_profile = {
            "themes": {"modes": ["light"], "defaultTheme": "light"},
            "archetype": "standard",
        }

    def _run() -> None:
        # T1 — Ingest: stage raw token files
        _ingest_tokens(output_dir)

        # T2 — Validate: DTCG schema, naming, WCAG contrast
        _validate_tokens(output_dir)

        # Guard: stop pipeline on fatal validation failures
        rejection_path = Path(output_dir) / "tokens" / "validation-rejection.json"
        if rejection_path.exists():
            data = json.loads(rejection_path.read_text(encoding="utf-8"))
            if data.get("fatal_count", 0) > 0:
                raise RuntimeError(
                    f"Token validation failed with {data['fatal_count']} fatal error(s). "
                    "See tokens/validation-rejection.json for details."
                )

        # T3 — Compile: produce CSS, SCSS, TS, JSON artefacts
        _compile_tokens(output_dir, brand_profile=brand_profile)

        # T4 — Integrity: cross-tier reference graph checks
        _check_integrity(output_dir)

        # T5 — Diff: generate change log against prior run
        _run_diff(output_dir)

    return StubCrew(name="token_engine", run_fn=_run)
