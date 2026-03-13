"""Tests for relationship_analyzer tool."""
from __future__ import annotations

import json


def test_cross_domain_dependency_detected(tmp_path):
    """Cross-domain dependency is detected from component-index.json."""
    from daf.tools.relationship_analyzer import analyze

    index = {
        "Select": {"dependencies": ["Popover"]},
        "Popover": {"dependencies": []},
    }
    index_path = tmp_path / "component-index.json"
    index_path.write_text(json.dumps(index))

    domain_map = {"Select": "forms", "Popover": "layout"}
    result = analyze(str(index_path), domain_map)

    cross_domain = [r for r in result if r["component"] == "Select"]
    assert len(cross_domain) == 1
    dep = cross_domain[0]
    assert dep["depends_on"] == "Popover"
    assert dep["component_domain"] == "forms"
    assert dep["dependency_domain"] == "layout"


def test_missing_component_index_returns_empty_list(tmp_path):
    """Missing component-index.json returns empty list without raising."""
    from daf.tools.relationship_analyzer import analyze

    missing_path = tmp_path / "nonexistent.json"
    result = analyze(str(missing_path), {})
    assert result == []
