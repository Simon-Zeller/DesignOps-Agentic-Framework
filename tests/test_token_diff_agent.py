"""Unit tests for Token Diff Agent (Agent 11) — TDD red phase."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def staged_tokens(tmp_path):
    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    base = {"color": {"brand": {"primary": {"$type": "color", "$value": "#005FCC"}}}}
    semantic = {
        "color": {
            "interactive": {
                "default": {"$type": "color", "$value": "{color.brand.primary}"},
            }
        }
    }
    (staged / "base.tokens.json").write_text(json.dumps(base))
    (staged / "semantic.tokens.json").write_text(json.dumps(semantic))
    (staged / "component.tokens.json").write_text(json.dumps({}))
    return tmp_path


def test_diff_json_always_written_on_completion(staged_tokens):
    """tokens/diff.json is always written, even on initial generation."""
    from daf.agents.token_diff import _run_diff

    _run_diff(str(staged_tokens))

    diff_file = staged_tokens / "tokens" / "diff.json"
    assert diff_file.exists()
    data = json.loads(diff_file.read_text())
    # Must be valid diff structure
    assert "added" in data or "is_initial_generation" in data
