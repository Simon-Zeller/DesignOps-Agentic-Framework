"""CrewSequencer — deterministic phase sequencer with I/O contract validation.

Drives the 8-crew pipeline in the order defined in PRD §3.1, validates
required input files before each invocation, and returns a list of CrewResult
objects. No retry logic — that is handled by run_first_publish_agent (Agent 6).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field as PydanticField


# ---------------------------------------------------------------------------
# CrewResult dataclass
# ---------------------------------------------------------------------------

@dataclass
class CrewResult:
    """Result object returned for each crew invocation."""

    crew: str
    status: str  # "success" | "failed" | "skipped" | "rejected" | "partial"
    reason: str | None = None
    rejection: dict | None = None
    retries_used: int = 0
    retries_exhausted: bool = False
    artifacts_written: list[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.monotonic)
    completed_at: float = field(default_factory=time.monotonic)


# ---------------------------------------------------------------------------
# I/O contract table (PRD §3.6)
# ---------------------------------------------------------------------------

CREW_IO_CONTRACTS: list[dict[str, Any]] = [
    {
        "name": "token_engine",
        "required_inputs": [
            "tokens/base.tokens.json",
            "tokens/semantic.tokens.json",
            "tokens/component.tokens.json",
        ],
        "optional_inputs": [],
        "phase": 1,
    },
    {
        "name": "design_to_code",
        "required_inputs": [
            "specs",
            "tokens/compiled",
        ],
        "optional_inputs": [],
        "phase": 2,
    },
    {
        "name": "component_factory",
        "required_inputs": [
            "specs",
            "tokens/semantic.tokens.json",
        ],
        "optional_inputs": [],
        "phase": 2,
    },
    {
        "name": "documentation",
        "required_inputs": [
            "specs",
        ],
        "optional_inputs": [
            "tokens/diff.json",
        ],
        "phase": 4,
    },
    {
        "name": "governance",
        "required_inputs": [
            "brand-profile.json",
            "pipeline-config.json",
            "docs",
        ],
        "optional_inputs": [],
        "phase": 4,
    },
    {
        "name": "ai_semantic_layer",
        "required_inputs": [
            "specs",
        ],
        "optional_inputs": [],
        "phase": 5,
    },
    {
        "name": "analytics",
        "required_inputs": [
            "specs",
        ],
        "optional_inputs": [],
        "phase": 5,
    },
    {
        "name": "release",
        "required_inputs": [],
        "optional_inputs": [],
        "phase": 6,
    },
]

# Map crew name → factory import path and function name (lazy import to avoid circular deps)
_CREW_FACTORY_MAP: dict[str, tuple[str, str]] = {
    "token_engine": ("daf.crews.token_engine", "create_token_engine_crew"),
    "design_to_code": ("daf.crews.design_to_code", "create_design_to_code_crew"),
    "component_factory": ("daf.crews.component_factory", "create_component_factory_crew"),
    "documentation": ("daf.crews.documentation", "create_documentation_crew"),
    "governance": ("daf.crews.governance", "create_governance_crew"),
    "ai_semantic_layer": ("daf.crews.ai_semantic_layer", "create_ai_semantic_layer_crew"),
    "analytics": ("daf.crews.analytics", "create_analytics_crew"),
    "release": ("daf.crews.release", "create_release_crew"),
}


def _get_factory(crew_name: str):
    """Lazily import and return the crew factory function."""
    module_path, func_name = _CREW_FACTORY_MAP[crew_name]
    import importlib

    mod = importlib.import_module(module_path)
    return getattr(mod, func_name)


def _check_io_contract(contract: dict[str, Any], output_dir: Path) -> str | None:
    """Return a missing-input reason string, or None if all required inputs exist."""
    for req in contract.get("required_inputs", []):
        if not (output_dir / req).exists():
            return f"missing_required_input: {req}"
    return None


# ---------------------------------------------------------------------------
# CrewSequencer tool
# ---------------------------------------------------------------------------

class CrewSequencer(BaseTool):
    """Deterministic tool that sequences all 8 downstream crews in phase order."""

    name: str = PydanticField(default="crew_sequencer")
    description: str = PydanticField(
        default=(
            "Runs all 8 downstream crews in phase order, validates I/O contracts "
            "before each invocation, and returns a list of CrewResult objects."
        )
    )

    def run_sequence(
        self,
        output_dir: str,
        start_phase: int = 1,
    ) -> list[CrewResult]:
        """Invoke all 8 crews in order from *start_phase*, returning CrewResult list.

        If a required input is missing for a crew, that crew is marked failed and all
        subsequent crews are skipped (fail-fast behaviour).
        """
        od = Path(output_dir)
        results: list[CrewResult] = []
        failed_fast = False

        for contract in CREW_IO_CONTRACTS:
            crew_name = contract["name"]
            phase = contract.get("phase", 0)

            if failed_fast:
                results.append(
                    CrewResult(crew=crew_name, status="skipped", reason="upstream failure")
                )
                continue

            # Skip phases before start_phase (for resume)
            if phase < start_phase:
                continue

            # Validate I/O contract
            missing_reason = _check_io_contract(contract, od)
            if missing_reason is not None:
                results.append(
                    CrewResult(crew=crew_name, status="failed", reason=missing_reason)
                )
                failed_fast = True
                continue

            # Invoke the crew
            factory = _get_factory(crew_name)
            crew = factory(output_dir=output_dir)

            result = crew.kickoff()

            if isinstance(result, CrewResult):
                results.append(result)
            else:
                # Stub crews return a string; treat as success
                results.append(
                    CrewResult(
                        crew=crew_name,
                        status="success",
                        artifacts_written=[],
                    )
                )

        return results

    def _run(self, output_dir: str, start_phase: int = 1) -> str:
        import json

        results = self.run_sequence(output_dir=output_dir, start_phase=start_phase)
        return json.dumps(
            [
                {
                    "crew": r.crew,
                    "status": r.status,
                    "reason": r.reason,
                    "retries_used": r.retries_used,
                }
                for r in results
            ]
        )
