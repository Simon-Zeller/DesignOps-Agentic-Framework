"""Agent 36 – VersionCalculator tool (Release Crew, Phase 6).

Derives a semver string from gate pass/fail results:
  - v1.0.0  when fatal_failed == 0
  - v0.1.0  when any fatal gate fails
  - v0.1.0-experimental on malformed input
"""
from __future__ import annotations

import json
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class VersionCalculator(BaseTool):
    """Derive a semantic version string from gate pass/fail results."""

    name: str = Field(default="version_calculator")
    description: str = Field(
        default=(
            "Accepts a JSON string with fatal_failed/fatal_passed counts and returns "
            "a semantic version string: v1.0.0 when all fatal gates pass, v0.1.0 when any "
            "fails, or v0.1.0-experimental on malformed input."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, gate_summary: str = "", **kwargs: Any) -> str:
        try:
            data: dict[str, Any] = json.loads(gate_summary)
            fatal_failed = int(data["fatal_failed"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return "v0.1.0-experimental"

        if fatal_failed == 0:
            return "v1.0.0"
        return "v0.1.0"
