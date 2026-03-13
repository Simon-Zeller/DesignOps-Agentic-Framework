"""Report Writer — serialises structured generation results to reports/generation-summary.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def write_generation_summary(
    results: list[dict[str, Any]],
    output_dir: str,
) -> None:
    """Write *results* to ``<output_dir>/reports/generation-summary.json``.

    Creates ``reports/`` if it does not exist. Always writes — even if all
    components failed.

    Args:
        results: List of per-component result dicts. Each should have
                 ``component``, ``files_written``, ``confidence``, and ``warnings``.
        output_dir: Root output directory.
    """
    reports_dir = Path(output_dir) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    total = len(results)
    generated = sum(1 for r in results if r.get("files_written"))
    failed = total - generated

    summary: dict[str, Any] = {
        "total_components": total,
        "generated": generated,
        "failed": failed,
        "components": results,
    }

    output_path = reports_dir / "generation-summary.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# ReportWriter BaseTool — governance/quality-gates.json
# ---------------------------------------------------------------------------


class _WriterInput(BaseModel):
    results: dict[str, Any]
    output_path: str


class ReportWriter(BaseTool):
    """Serialize quality gate results to governance/quality-gates.json."""

    name: str = "governance_report_writer"
    description: str = (
        "Serializes per-component quality gate results to the given output_path as JSON. "
        "Creates parent directories if needed."
    )
    args_schema: type[BaseModel] = _WriterInput

    def _run(
        self,
        results: dict[str, Any],
        output_path: str,
        **kwargs: Any,
    ) -> str:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        return str(out)
