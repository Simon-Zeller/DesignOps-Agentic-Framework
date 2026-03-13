"""Agent 36 – GateStatusReader tool (Release Crew, Phase 6).

Reads reports/governance/quality-gates.json and returns structured pass/fail
counts. Returns an all-zero safe default when the file is absent.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class GateStatusReader(BaseTool):
    """Read and normalise quality-gates.json into pass/fail counts."""

    name: str = Field(default="gate_status_reader")
    description: str = Field(
        default=(
            "Reads reports/governance/quality-gates.json from the output directory "
            "and returns fatal/warning pass/fail counts. Returns safe all-zero default "
            "with a warnings entry when the file is absent."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, _input: str = "", **kwargs: Any) -> dict[str, Any]:
        gate_path = Path(self.output_dir) / "reports" / "governance" / "quality-gates.json"
        if not gate_path.exists():
            return {
                "fatal_passed": 0,
                "fatal_failed": 0,
                "warning_passed": 0,
                "warning_failed": 0,
                "gates": [],
                "warnings": ["quality-gates.json not found; using safe default (fallback to v0.1.0-experimental)"],
            }

        try:
            data = json.loads(gate_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {
                "fatal_passed": 0,
                "fatal_failed": 0,
                "warning_passed": 0,
                "warning_failed": 0,
                "gates": [],
                "warnings": ["quality-gates.json could not be parsed; using safe default"],
            }

        gates: list[dict[str, Any]] = data.get("gates", [])

        fatal_passed = sum(
            1 for g in gates if g.get("severity") == "fatal" and g.get("passed", False)
        )
        fatal_failed = sum(
            1 for g in gates if g.get("severity") == "fatal" and not g.get("passed", True)
        )
        warning_passed = sum(
            1 for g in gates if g.get("severity") == "warning" and g.get("passed", False)
        )
        warning_failed = sum(
            1 for g in gates if g.get("severity") == "warning" and not g.get("passed", True)
        )

        return {
            "fatal_passed": fatal_passed,
            "fatal_failed": fatal_failed,
            "warning_passed": warning_passed,
            "warning_failed": warning_failed,
            "gates": gates,
        }
