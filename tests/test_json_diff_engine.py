"""Unit tests for JsonDiffEngine tool — TDD red phase."""
from __future__ import annotations

import pytest


@pytest.fixture
def token_set_10():
    """A flat token dict with 10 entries."""
    return {f"color.palette.{i:02d}": {"$type": "color", "$value": f"#{i:06x}"} for i in range(10)}


def test_initial_generation_classifies_all_as_added(token_set_10):
    """With prior=None, every token is classified as added; is_initial_generation is True."""
    from daf.tools.json_diff_engine import JsonDiffEngine

    result = JsonDiffEngine()._run(current=token_set_10, prior=None)
    assert result["is_initial_generation"] is True
    assert len(result["added"]) == 10
    assert result["modified"] == []
    assert result["removed"] == []
    assert result["deprecated"] == []


def test_modified_token_appears_in_modified_list():
    """A changed $value appears in modified[] with old and new values."""
    from daf.tools.json_diff_engine import JsonDiffEngine

    prior = {"color.brand.primary": {"$type": "color", "$value": "#005FCC"}}
    current = {"color.brand.primary": {"$type": "color", "$value": "#0066FF"}}
    result = JsonDiffEngine()._run(current=current, prior=prior)
    assert result["is_initial_generation"] is False
    assert len(result["modified"]) == 1
    entry = result["modified"][0]
    assert entry["token_path"] == "color.brand.primary"
    assert entry["old_value"] == "#005FCC"
    assert entry["new_value"] == "#0066FF"


def test_removed_token_appears_in_removed_list():
    """A token present in prior but absent in current appears in removed[]."""
    from daf.tools.json_diff_engine import JsonDiffEngine

    prior = {
        "color.brand.primary": {"$type": "color", "$value": "#005FCC"},
        "color.brand.secondary": {"$type": "color", "$value": "#FF6600"},
    }
    current = {
        "color.brand.primary": {"$type": "color", "$value": "#005FCC"},
    }
    result = JsonDiffEngine()._run(current=current, prior=prior)
    removed_paths = [r["token_path"] for r in result["removed"]]
    assert "color.brand.secondary" in removed_paths
