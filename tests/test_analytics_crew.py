"""Integration tests for Analytics Crew factory (p15-analytics-crew, TDD red phase)."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_crew_raises_runtime_error_when_no_spec_files_exist(tmp_path):
    """RuntimeError raised when specs/ directory is absent."""
    from daf.crews.analytics import create_analytics_crew

    with pytest.raises(RuntimeError, match="specs"):
        create_analytics_crew(str(tmp_path))


def test_crew_raises_runtime_error_when_specs_dir_empty(tmp_path):
    """RuntimeError raised when specs/ exists but has no .spec.yaml files."""
    from daf.crews.analytics import create_analytics_crew

    (tmp_path / "specs").mkdir()

    with pytest.raises(RuntimeError, match="specs"):
        create_analytics_crew(str(tmp_path))


def test_crew_returns_crewai_crew_when_specs_exist(tmp_path):
    """create_analytics_crew returns a crewai.Crew (not a StubCrew) when specs exist."""
    from crewai import Crew

    from daf.crews.analytics import create_analytics_crew

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text("name: Button\nprops:\n  - name: disabled\n    type: boolean\n")

    crew = create_analytics_crew(str(tmp_path))
    assert isinstance(crew, Crew)


def test_crew_has_five_agents_and_five_tasks(tmp_path):
    """The returned crew has exactly 5 agents and 5 tasks."""
    from daf.crews.analytics import create_analytics_crew

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text("name: Button\nprops:\n  - name: disabled\n    type: boolean\n")

    crew = create_analytics_crew(str(tmp_path))
    assert len(crew.agents) == 5
    assert len(crew.tasks) == 5
