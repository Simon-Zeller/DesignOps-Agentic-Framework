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


def test_diff_with_prior_runs_correctly(tmp_path):
    """_run_diff handles an existing diff.json gracefully (no crash)."""
    from daf.agents.token_diff import _run_diff

    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    base = {"color": {"brand": {"primary": {"$type": "color", "$value": "#005FCC"}}}}
    (staged / "base.tokens.json").write_text(json.dumps(base))
    (staged / "semantic.tokens.json").write_text(json.dumps({}))
    (staged / "component.tokens.json").write_text(json.dumps({}))

    # Write a pre-existing diff.json (empty prior snapshot look-alike)
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir(parents=True, exist_ok=True)
    prior_diff = {"is_initial_generation": True, "added": [], "modified": [], "removed": [], "deprecated": []}
    (tokens_dir / "diff.json").write_text(json.dumps(prior_diff))

    _run_diff(str(tmp_path))

    diff_file = tokens_dir / "diff.json"
    assert diff_file.exists()
    data = json.loads(diff_file.read_text())
    assert "added" in data


def test_create_token_diff_agent_returns_non_none(tmp_path):
    """create_token_diff_agent returns a non-None Agent object."""
    from daf.agents.token_diff import create_token_diff_agent, create_token_diff_task

    with patch("daf.agents.token_diff.Agent") as mock_agent_cls, \
         patch("daf.agents.token_diff.Task") as mock_task_cls:
        agent = create_token_diff_agent()
        task = create_token_diff_task(output_dir=str(tmp_path))
        assert agent is not None
        assert task is not None

