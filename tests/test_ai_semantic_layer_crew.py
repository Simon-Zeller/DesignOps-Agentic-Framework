"""Integration tests for AI Semantic Layer Crew factory (p16-ai-semantic-layer-crew, TDD red phase)."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_crew_raises_runtime_error_when_no_spec_files_exist(tmp_path):
    """RuntimeError raised when specs/ directory is absent."""
    from daf.crews.ai_semantic_layer import create_ai_semantic_layer_crew

    with pytest.raises(RuntimeError, match="specs"):
        create_ai_semantic_layer_crew(str(tmp_path))


def test_crew_raises_runtime_error_when_specs_dir_empty(tmp_path):
    """RuntimeError raised when specs/ exists but has no .spec.yaml files."""
    from daf.crews.ai_semantic_layer import create_ai_semantic_layer_crew

    (tmp_path / "specs").mkdir()

    with pytest.raises(RuntimeError, match="specs"):
        create_ai_semantic_layer_crew(str(tmp_path))


def test_crew_returns_crewai_crew_when_specs_exist(tmp_path):
    """create_ai_semantic_layer_crew returns a crewai.Crew when specs exist."""
    from crewai import Crew

    from daf.crews.ai_semantic_layer import create_ai_semantic_layer_crew

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text(
        "name: Button\nprops:\n  - name: disabled\n    type: boolean\n"
    )

    crew = create_ai_semantic_layer_crew(str(tmp_path))
    assert isinstance(crew, Crew)


def test_crew_has_five_agents_and_five_tasks(tmp_path):
    """The returned crew has exactly 5 agents and 5 tasks."""
    from daf.crews.ai_semantic_layer import create_ai_semantic_layer_crew

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text(
        "name: Button\nprops:\n  - name: disabled\n    type: boolean\n"
    )

    crew = create_ai_semantic_layer_crew(str(tmp_path))
    assert len(crew.agents) == 5
    assert len(crew.tasks) == 5


def test_crew_creates_registry_directory(tmp_path):
    """Factory creates the registry/ directory under output_dir."""
    from daf.crews.ai_semantic_layer import create_ai_semantic_layer_crew

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text(
        "name: Button\nprops:\n  - name: disabled\n    type: boolean\n"
    )

    create_ai_semantic_layer_crew(str(tmp_path))
    assert (tmp_path / "registry").is_dir()
