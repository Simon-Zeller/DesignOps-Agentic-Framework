"""Agent 37 – QualityReportParser tool (Release Crew, Phase 6).

Parses reports/governance/quality-gates.json into structured
{passed_gates, failed_gates, warnings} groupings.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class QualityReportParser(BaseTool):
    """Parse quality gate JSON into structured passed/failed/warnings summary."""

    name: str = Field(default="quality_report_parser")
    description: str = Field(
        default=(
            "Reads reports/governance/quality-gates.json and returns a structured dict "
            "with passed_gates (list of gate names), failed_gates, and warnings. "
            "Returns empty lists when the report file is absent."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, _input: str = "", **kwargs: Any) -> dict[str, Any]:
        gate_path = Path(self.output_dir) / "reports" / "governance" / "quality-gates.json"
        if not gate_path.exists():
            return {"passed_gates": [], "failed_gates": [], "warnings": []}

        try:
            data = json.loads(gate_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"passed_gates": [], "failed_gates": [], "warnings": []}

        gates: list[dict[str, Any]] = data.get("gates", [])
        passed: list[str] = []
        failed: list[str] = []
        warnings: list[str] = []

        for gate in gates:
            name = gate.get("name", "unknown")
            severity = gate.get("severity", "fatal")
            is_passed = gate.get("passed", False)

            if severity == "warning":
                if not is_passed:
                    warnings.append(name)
                else:
                    passed.append(name)
            else:
                if is_passed:
                    passed.append(name)
                else:
                    failed.append(name)

        return {"passed_gates": passed, "failed_gates": failed, "warnings": warnings}
