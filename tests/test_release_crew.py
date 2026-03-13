"""Tests for Release Crew factory (p17-release-crew, TDD red phase)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import crewai


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_output_dir(tmp_path: Path) -> Path:
    gate_dir = tmp_path / "reports" / "governance"
    gate_dir.mkdir(parents=True)
    (gate_dir / "quality-gates.json").write_text(
        json.dumps({"gates": [], "fatal_passed": 8, "fatal_failed": 0})
    )
    return tmp_path


# ---------------------------------------------------------------------------
# test_crew_raises_runtime_error_when_gate_report_missing
# ---------------------------------------------------------------------------

def test_crew_raises_runtime_error_when_gate_report_missing(tmp_path: Path) -> None:
    """Pre-flight guard raises RuntimeError when quality-gates.json is absent."""
    from daf.crews.release import create_release_crew

    with pytest.raises(RuntimeError, match="quality-gates.json"):
        create_release_crew(str(tmp_path))


# ---------------------------------------------------------------------------
# test_crew_returns_crewai_crew_when_gate_report_exists
# ---------------------------------------------------------------------------

def test_crew_returns_crewai_crew_when_gate_report_exists(tmp_path: Path) -> None:
    """Factory returns a real crewai.Crew when gate report is present."""
    _make_output_dir(tmp_path)
    from daf.crews.release import create_release_crew

    crew = create_release_crew(str(tmp_path))
    assert isinstance(crew, crewai.Crew)


# ---------------------------------------------------------------------------
# test_crew_has_four_agents_and_six_tasks
# ---------------------------------------------------------------------------

def test_crew_has_four_agents_and_six_tasks(tmp_path: Path) -> None:
    """Crew has exactly 4 agents and 6 tasks."""
    _make_output_dir(tmp_path)
    from daf.crews.release import create_release_crew

    crew = create_release_crew(str(tmp_path))
    assert len(crew.agents) == 4
    assert len(crew.tasks) == 6


# ---------------------------------------------------------------------------
# test_crew_creates_docs_and_codemods_directories
# ---------------------------------------------------------------------------

def test_crew_creates_docs_and_codemods_directories(tmp_path: Path) -> None:
    """Factory creates docs/ and docs/codemods/ directories in output_dir."""
    _make_output_dir(tmp_path)
    from daf.crews.release import create_release_crew

    create_release_crew(str(tmp_path))
    assert (tmp_path / "docs").is_dir()
    assert (tmp_path / "docs" / "codemods").is_dir()


# ---------------------------------------------------------------------------
# test_crew_does_not_include_rollback_agent
# ---------------------------------------------------------------------------

def test_crew_does_not_include_rollback_agent(tmp_path: Path) -> None:
    """None of the crew's agents should have rollback/checkpoint roles."""
    _make_output_dir(tmp_path)
    from daf.crews.release import create_release_crew

    crew = create_release_crew(str(tmp_path))
    for agent in crew.agents:
        role_lower = agent.role.lower()
        assert "rollback" not in role_lower
        assert "checkpoint manager" not in role_lower
