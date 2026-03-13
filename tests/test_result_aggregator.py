"""Tests for ResultAggregator tool (p09-pipeline-orchestrator, TDD red phase)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from daf.tools.crew_sequencer import CrewResult
from daf.tools.result_aggregator import ResultAggregator


def _success_result(crew: str) -> CrewResult:
    return CrewResult(
        crew=crew,
        status="success",
        retries_used=0,
        artifacts_written=[f"{crew}/output.json"],
    )


def _eight_successes() -> list[CrewResult]:
    return [
        _success_result("token_engine"),
        _success_result("design_to_code"),
        _success_result("component_factory"),
        _success_result("documentation"),
        _success_result("governance"),
        _success_result("ai_semantic_layer"),
        _success_result("analytics"),
        _success_result("release"),
    ]


# ---------------------------------------------------------------------------
# test_result_aggregator_all_success_writes_summary
# ---------------------------------------------------------------------------

def test_result_aggregator_all_success_writes_summary(tmp_path: Path) -> None:
    """All crews success → pipeline.status == 'success', 8 phase_results entries."""
    ra = ResultAggregator()
    ra.aggregate(crew_results=_eight_successes(), output_dir=str(tmp_path))

    summary_path = tmp_path / "reports" / "generation-summary.json"
    assert summary_path.exists()

    data = json.loads(summary_path.read_text())
    assert data["pipeline"]["status"] == "success"
    assert len(data["phase_results"]) == 8
    assert "started_at" in data["pipeline"]
    assert "completed_at" in data["pipeline"]


# ---------------------------------------------------------------------------
# test_result_aggregator_phase56_failure_yields_partial
# ---------------------------------------------------------------------------

def test_result_aggregator_phase56_failure_yields_partial(tmp_path: Path) -> None:
    """Phase 5 analytics failure → pipeline.status == 'partial'."""
    results = _eight_successes()
    # Analytics Crew (phase 5) fails — non-fatal
    results[6] = CrewResult(
        crew="analytics",
        status="failed",
        retries_used=2,
        retries_exhausted=True,
        artifacts_written=[],
    )

    ra = ResultAggregator()
    ra.aggregate(crew_results=results, output_dir=str(tmp_path))

    data = json.loads((tmp_path / "reports" / "generation-summary.json").read_text())
    assert data["pipeline"]["status"] == "partial"


# ---------------------------------------------------------------------------
# test_result_aggregator_phase13_failure_yields_failed
# ---------------------------------------------------------------------------

def test_result_aggregator_phase13_failure_yields_failed(tmp_path: Path) -> None:
    """Phase 1-3 retries exhausted → pipeline.status == 'failed'."""
    results = _eight_successes()
    results[0] = CrewResult(
        crew="token_engine",
        status="failed",
        retries_used=3,
        retries_exhausted=True,
        artifacts_written=[],
    )

    ra = ResultAggregator()
    ra.aggregate(crew_results=results, output_dir=str(tmp_path))

    data = json.loads((tmp_path / "reports" / "generation-summary.json").read_text())
    assert data["pipeline"]["status"] == "failed"


# ---------------------------------------------------------------------------
# test_result_aggregator_is_idempotent
# ---------------------------------------------------------------------------

def test_result_aggregator_is_idempotent(tmp_path: Path) -> None:
    """Calling aggregate twice overwrites without error."""
    ra = ResultAggregator()
    ra.aggregate(crew_results=_eight_successes(), output_dir=str(tmp_path))

    # Second call with a different result set
    results_v2 = _eight_successes()
    results_v2[6] = CrewResult(
        crew="analytics",
        status="failed",
        retries_used=1,
        retries_exhausted=False,
        artifacts_written=[],
    )

    # Should NOT raise
    ra.aggregate(crew_results=results_v2, output_dir=str(tmp_path))

    data = json.loads((tmp_path / "reports" / "generation-summary.json").read_text())
    assert data["pipeline"]["status"] == "partial"


# ---------------------------------------------------------------------------
# test_result_aggregator_empty_crew_result_list_raises
# ---------------------------------------------------------------------------

def test_result_aggregator_empty_crew_result_list_raises(tmp_path: Path) -> None:
    """Empty crew result list raises ValueError."""
    ra = ResultAggregator()
    with pytest.raises(ValueError, match=r"(?i)empty|no crew|at least"):
        ra.aggregate(crew_results=[], output_dir=str(tmp_path))
