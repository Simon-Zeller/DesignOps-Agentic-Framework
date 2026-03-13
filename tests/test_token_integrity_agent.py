"""Unit tests for Token Integrity Agent (Agent 10) — TDD red phase."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def staged_clean_tokens(tmp_path):
    """Three valid staged token files with no integrity violations."""
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


def test_clean_integrity_run_writes_report_with_zero_counts(staged_clean_tokens):
    """Clean token set produces integrity-report.json with fatal_count: 0."""
    from daf.agents.token_integrity import _check_integrity

    _check_integrity(str(staged_clean_tokens))

    report = staged_clean_tokens / "tokens" / "integrity-report.json"
    assert report.exists()
    data = json.loads(report.read_text())
    assert data["fatal_count"] == 0
    assert data["warning_count"] == 0


def test_tier_skip_violation_writes_fatal_to_rejection_file(tmp_path):
    """Component token directly referencing a base token produces a fatal tier-skip entry."""
    from daf.agents.token_integrity import _check_integrity

    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    base = {"color": {"brand": {"primary": {"$type": "color", "$value": "#005FCC"}}}}
    semantic = {}
    # Tier skip: component references base directly (skips semantic)
    component = {
        "button": {
            "background": {"$type": "color", "$value": "{color.brand.primary}"},
        }
    }
    (staged / "base.tokens.json").write_text(json.dumps(base))
    (staged / "semantic.tokens.json").write_text(json.dumps(semantic))
    (staged / "component.tokens.json").write_text(json.dumps(component))

    _check_integrity(str(tmp_path))

    rejection = tmp_path / "tokens" / "validation-rejection.json"
    assert rejection.exists()
    data = json.loads(rejection.read_text())
    checks = [f["check"] for f in data["failures"]]
    assert "reference_integrity" in checks or "tier_skip" in checks
    assert data["fatal_count"] >= 1


def test_agent10_appends_to_existing_rejection_file(tmp_path):
    """Agent 10 merges its violations into an existing rejection file from Agent 8."""
    from daf.agents.token_integrity import _check_integrity

    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    base = {"color": {"brand": {"primary": {"$type": "color", "$value": "#005FCC"}}}}
    semantic = {}
    # Tier skip produces a new fatal from Agent 10
    component = {
        "button": {
            "bg": {"$type": "color", "$value": "{color.brand.primary}"},
        }
    }
    (staged / "base.tokens.json").write_text(json.dumps(base))
    (staged / "semantic.tokens.json").write_text(json.dumps(semantic))
    (staged / "component.tokens.json").write_text(json.dumps(component))

    # Pre-existing rejection file from Agent 8
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir(parents=True, exist_ok=True)
    existing_rejection = {
        "phase": "token-validation",
        "agent": 8,
        "attempt": 1,
        "timestamp": "2026-01-01T00:00:00Z",
        "failures": [{"check": "dtcg_schema", "severity": "fatal", "token_path": "x", "detail": "missing $type", "suggestion": ""}],
        "fatal_count": 1,
        "warning_count": 0,
    }
    (tokens_dir / "validation-rejection.json").write_text(json.dumps(existing_rejection))

    _check_integrity(str(tmp_path))

    rejection = tokens_dir / "validation-rejection.json"
    data = json.loads(rejection.read_text())
    assert data["fatal_count"] >= 2
