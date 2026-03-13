"""ResultAggregator — merges per-crew CrewResult objects into generation-summary.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from crewai.tools import BaseTool
from pydantic import Field

if TYPE_CHECKING:
    from daf.tools.crew_sequencer import CrewResult

# Crews in Phases 1–3 whose failure makes the pipeline status "failed"
_CRITICAL_CREWS = frozenset({"token_engine", "design_to_code", "component_factory"})


class ResultAggregator(BaseTool):
    """Deterministic tool that merges CrewResult list into generation-summary.json."""

    name: str = Field(default="result_aggregator")
    description: str = Field(
        default=(
            "Merges per-crew CrewResult objects into reports/generation-summary.json. "
            "Determines pipeline.status: 'success', 'partial', or 'failed'."
        )
    )

    def aggregate(self, crew_results: list["CrewResult"], output_dir: str) -> dict[str, Any]:
        """Write reports/generation-summary.json and return the summary dict.

        Raises ValueError if crew_results is empty.
        """
        if not crew_results:
            raise ValueError("crew_results must not be empty — at least one CrewResult is required.")

        started_at = _iso_now()
        completed_at = _iso_now()

        phase_results = []
        pipeline_status = "success"

        for result in crew_results:
            entry = {
                "crew": result.crew,
                "status": result.status,
                "retries_used": result.retries_used,
                "retries_exhausted": result.retries_exhausted,
                "artifacts_written": list(result.artifacts_written),
            }
            phase_results.append(entry)

            # Determine pipeline status from this result
            if result.status == "failed" and result.retries_exhausted:
                if result.crew in _CRITICAL_CREWS:
                    pipeline_status = "failed"
                elif pipeline_status != "failed":
                    pipeline_status = "partial"
            elif result.status == "failed":
                if result.crew in _CRITICAL_CREWS:
                    pipeline_status = "failed"
                elif pipeline_status != "failed":
                    pipeline_status = "partial"

        summary = {
            "pipeline": {
                "status": pipeline_status,
                "started_at": started_at,
                "completed_at": completed_at,
            },
            "phase_results": phase_results,
        }

        out_path = Path(output_dir) / "reports" / "generation-summary.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2))

        return summary

    def _run(self, crew_results_json: str, output_dir: str) -> str:
        """BaseTool entry point — receives JSON-serialised CrewResult list."""
        from daf.tools.crew_sequencer import CrewResult as CR

        raw: list[dict[str, Any]] = json.loads(crew_results_json)
        results = [
            CR(
                crew=r["crew"],
                status=r["status"],
                retries_used=r.get("retries_used", 0),
                retries_exhausted=r.get("retries_exhausted", False),
                artifacts_written=r.get("artifacts_written", []),
            )
            for r in raw
        ]
        summary = self.aggregate(results, output_dir)
        return json.dumps(summary)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()
