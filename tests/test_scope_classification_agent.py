"""Unit tests for scope_classification agent — produces priority queue JSON (mocked LLM)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


def _write_fixture_specs(specs_dir: Path) -> None:
    specs_dir.mkdir(parents=True, exist_ok=True)
    (specs_dir / "box.spec.yaml").write_text("component: Box\n")
    (specs_dir / "button.spec.yaml").write_text(
        "component: Button\nvariants:\n  - primary\n  - secondary\n"
    )
    (specs_dir / "datagrid.spec.yaml").write_text(
        "component: DataGrid\nvariants:\n  - compact\n  - comfortable\n  - spacious\n  - dense\n  - wide\n"
    )


def test_scope_classification_agent_produces_priority_queue(tmp_path):
    """Agent writes scope_classifier_output.json with Box before Button before DataGrid."""
    from daf.agents.scope_classification import _classify_specs

    specs_dir = tmp_path / "specs"
    _write_fixture_specs(specs_dir)

    _classify_specs(str(tmp_path))

    output = tmp_path / "scope_classifier_output.json"
    assert output.exists(), "scope_classifier_output.json was not created"

    data = json.loads(output.read_text())
    names = [c["name"] for c in data["components"]]
    assert "Box" in names
    assert "Button" in names
    assert "DataGrid" in names
    # Box (primitive) should come before DataGrid (complex)
    assert names.index("Box") < names.index("DataGrid")
