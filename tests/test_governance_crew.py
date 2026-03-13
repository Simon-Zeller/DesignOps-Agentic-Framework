"""Integration tests for Governance Crew factory pre-flight guard."""
from __future__ import annotations

import json
import pytest


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_crew_raises_runtime_error_when_component_index_absent(tmp_path):
    """RuntimeError raised when docs/component-index.json is missing."""
    from daf.crews.governance import create_governance_crew

    with pytest.raises(RuntimeError, match="Documentation Crew output not found"):
        create_governance_crew(str(tmp_path))


def test_crew_instantiates_when_component_index_present(tmp_path):
    """Crew is returned without error when docs/component-index.json exists."""
    from daf.crews.governance import create_governance_crew

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "component-index.json").write_text(json.dumps({"Button": {}}))

    crew = create_governance_crew(str(tmp_path))
    assert crew is not None
