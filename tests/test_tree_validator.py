"""Unit tests for TreeValidator tool (p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import pytest


def test_tree_validator_returns_valid_for_conforming_tree(tmp_path):
    """TreeValidator returns valid=True for a tree that follows composition rules."""
    from daf.tools.tree_validator import TreeValidator

    rules = [
        {
            "component": "Card",
            "allowed_children": ["Text", "Button"],
            "forbidden_children": [],
        }
    ]
    tree = {"component": "Card", "children": [{"component": "Text"}]}

    validator = TreeValidator()
    result = validator._run(tree=tree, rules=rules, output_dir=str(tmp_path))

    assert isinstance(result, dict)
    assert result["valid"] is True
    assert result["violations"] == []


def test_tree_validator_returns_violation_for_forbidden_nesting(tmp_path):
    """TreeValidator returns violations for trees with forbidden nesting."""
    from daf.tools.tree_validator import TreeValidator

    rules = [
        {
            "component": "Button",
            "allowed_children": [],
            "forbidden_children": ["Button"],
        }
    ]
    tree = {"component": "Button", "children": [{"component": "Button"}]}

    validator = TreeValidator()
    result = validator._run(tree=tree, rules=rules, output_dir=str(tmp_path))

    assert isinstance(result, dict)
    assert result["valid"] is False
    assert len(result["violations"]) >= 1


def test_tree_validator_returns_valid_for_empty_children(tmp_path):
    """TreeValidator returns valid=True for a leaf component with no children."""
    from daf.tools.tree_validator import TreeValidator

    rules = [
        {
            "component": "Button",
            "allowed_children": [],
            "forbidden_children": [],
        }
    ]
    tree = {"component": "Button", "children": []}

    validator = TreeValidator()
    result = validator._run(tree=tree, rules=rules, output_dir=str(tmp_path))

    assert result["valid"] is True
