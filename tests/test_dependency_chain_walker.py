"""Unit tests for DependencyChainWalker tool."""
from __future__ import annotations

import json


def test_dependency_chain_walker_root_cause_failure(tmp_path):
    """Component with no dependencies is classified as root-cause."""
    from daf.tools.dependency_chain_walker import DependencyChainWalker

    graph = {"Button": {"dependencies": []}, "Card": {"dependencies": ["Button"]}}
    graph_file = tmp_path / "dependency_graph.json"
    graph_file.write_text(json.dumps(graph))

    result = DependencyChainWalker()._run(str(tmp_path), ["Button"])
    btn = next(f for f in result["failures"] if f["component"] == "Button")
    assert btn["classification"] == "root-cause"
    assert "Button" in btn["dependency_chain"]


def test_dependency_chain_walker_downstream_failure(tmp_path):
    """Component whose dependency also failed is classified as downstream."""
    from daf.tools.dependency_chain_walker import DependencyChainWalker

    graph = {"Button": {"dependencies": []}, "Card": {"dependencies": ["Button"]}}
    graph_file = tmp_path / "dependency_graph.json"
    graph_file.write_text(json.dumps(graph))

    result = DependencyChainWalker()._run(str(tmp_path), ["Button", "Card"])
    card = next(f for f in result["failures"] if f["component"] == "Card")
    assert card["classification"] == "downstream"
    assert "Button" in card["dependency_chain"]
    assert card["root_cause_component"] == "Button"


def test_dependency_chain_walker_no_failures_returns_empty(tmp_path):
    """Empty failures set returns empty failures list without raising."""
    from daf.tools.dependency_chain_walker import DependencyChainWalker

    graph = {"Button": {"dependencies": []}}
    (tmp_path / "dependency_graph.json").write_text(json.dumps(graph))

    result = DependencyChainWalker()._run(str(tmp_path), [])
    assert result["failures"] == []


def test_dependency_chain_walker_handles_missing_graph_file(tmp_path):
    """Returns empty failures list when dependency_graph.json does not exist."""
    from daf.tools.dependency_chain_walker import DependencyChainWalker

    result = DependencyChainWalker()._run(str(tmp_path), ["Button"])
    assert "failures" in result
