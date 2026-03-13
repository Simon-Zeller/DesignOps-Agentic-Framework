"""Agent 40 – RollbackReporter tool (Release Crew, Phase 6).

Accepts a dict with restored_phase, failed_crew, reason.
Writes reports/rollback-log.json; appends to existing log if present.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class RollbackReporter(BaseTool):
    """Write rollback details to reports/rollback-log.json."""

    name: str = Field(default="rollback_reporter")
    description: str = Field(
        default=(
            "Accepts a JSON string with restored_phase, failed_crew, and reason keys. "
            "Writes (or appends to) reports/rollback-log.json in output_dir."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, report_json: str = "", **kwargs: Any) -> str:
        try:
            entry: dict[str, Any] = json.loads(report_json)
        except (json.JSONDecodeError, TypeError):
            entry = {"raw": report_json}

        reports_dir = Path(self.output_dir) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        log_path = reports_dir / "rollback-log.json"

        existing: list[dict[str, Any]] = []
        if log_path.exists():
            try:
                data = json.loads(log_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    existing = data
                elif isinstance(data, dict):
                    existing = [data]
            except (json.JSONDecodeError, OSError):
                existing = []

        existing.append(entry)
        log_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        return str(log_path)
