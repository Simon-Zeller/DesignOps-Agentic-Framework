"""Unit tests for Token Validation Agent (Agent 8) — TDD red phase."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


REJECTION_SCHEMA_KEYS = {"phase", "agent", "attempt", "timestamp", "failures", "fatal_count", "warning_count"}


@pytest.fixture
def staged_clean_tokens(tmp_path):
    """Write three valid staged DTCG files to tokens/staged/."""
    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    base = {
        "color": {
            "brand": {
                "primary": {"$type": "color", "$value": "#005FCC"},
            }
        }
    }
    semantic = {
        "color": {
            "interactive": {
                "default": {"$type": "color", "$value": "{color.brand.primary}"},
            }
        }
    }
    component = {}
    (staged / "base.tokens.json").write_text(json.dumps(base))
    (staged / "semantic.tokens.json").write_text(json.dumps(semantic))
    (staged / "component.tokens.json").write_text(json.dumps(component))
    return tmp_path


def test_clean_staged_tokens_no_rejection_file(staged_clean_tokens):
    """No validation-rejection.json is written when staged tokens are clean."""
    from daf.agents.token_validation import _validate_tokens

    _validate_tokens(str(staged_clean_tokens))
    rejection = staged_clean_tokens / "tokens" / "validation-rejection.json"
    assert not rejection.exists()


def test_fatal_violation_writes_rejection_file_with_correct_schema(tmp_path):
    """DTCG fatal violation causes rejection file with correct schema keys."""
    from daf.agents.token_validation import _validate_tokens

    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    # Token missing $type — DTCG fatal
    bad_doc = {"color": {"brand": {"primary": {"$value": "#005FCC"}}}}
    (staged / "base.tokens.json").write_text(json.dumps(bad_doc))
    (staged / "semantic.tokens.json").write_text(json.dumps({}))
    (staged / "component.tokens.json").write_text(json.dumps({}))

    _validate_tokens(str(tmp_path))

    rejection = tmp_path / "tokens" / "validation-rejection.json"
    assert rejection.exists()
    data = json.loads(rejection.read_text())
    assert REJECTION_SCHEMA_KEYS.issubset(data.keys())
    assert data["fatal_count"] >= 1


def test_stale_rejection_file_deleted_on_clean_validation(staged_clean_tokens):
    """Stale rejection file from prior run is deleted when validation passes."""
    from daf.agents.token_validation import _validate_tokens

    rejection = staged_clean_tokens / "tokens" / "validation-rejection.json"
    rejection.parent.mkdir(parents=True, exist_ok=True)
    rejection.write_text(json.dumps({"stale": True}))

    _validate_tokens(str(staged_clean_tokens))

    assert not rejection.exists()


def test_wcag_contrast_failure_produces_fatal_violation(tmp_path):
    """Low contrast pair produces fatal violation with check: wcag_contrast."""
    from daf.agents.token_validation import _validate_tokens

    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    # Tokens with a declared low-contrast pair annotation
    semantic = {
        "color": {
            "interactive": {
                "foreground": {
                    "$type": "color",
                    "$value": "#CCCCCC",
                    "$extensions": {
                        "com.daf.contrast-pair": {
                            "background": "color.interactive.background",
                        }
                    },
                },
                "background": {"$type": "color", "$value": "#BBBBBB"},
            }
        }
    }
    (staged / "base.tokens.json").write_text(json.dumps({}))
    (staged / "semantic.tokens.json").write_text(json.dumps(semantic))
    (staged / "component.tokens.json").write_text(json.dumps({}))

    _validate_tokens(str(tmp_path))

    rejection = tmp_path / "tokens" / "validation-rejection.json"
    assert rejection.exists()
    data = json.loads(rejection.read_text())
    checks = [f["check"] for f in data["failures"]]
    assert "wcag_contrast" in checks


def test_no_colour_pairs_emits_warning_not_fatal(tmp_path):
    """Absence of contrast pair annotations is a warning, not fatal."""
    from daf.agents.token_validation import _validate_tokens

    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    base = {"scale": {"spacing": {"4": {"$type": "dimension", "$value": "16px"}}}}
    (staged / "base.tokens.json").write_text(json.dumps(base))
    (staged / "semantic.tokens.json").write_text(json.dumps({}))
    (staged / "component.tokens.json").write_text(json.dumps({}))

    _validate_tokens(str(tmp_path))

    rejection = tmp_path / "tokens" / "validation-rejection.json"
    assert not rejection.exists()


def test_empty_tier_file_produces_fatal_violation(tmp_path):
    """Empty base token tier produces a fatal violation."""
    from daf.agents.token_validation import _validate_tokens

    staged = tmp_path / "tokens" / "staged"
    staged.mkdir(parents=True, exist_ok=True)
    (staged / "base.tokens.json").write_text(json.dumps({}))  # empty
    (staged / "semantic.tokens.json").write_text(json.dumps({}))
    (staged / "component.tokens.json").write_text(json.dumps({}))

    _validate_tokens(str(tmp_path))

    rejection = tmp_path / "tokens" / "validation-rejection.json"
    assert rejection.exists()
    data = json.loads(rejection.read_text())
    assert data["fatal_count"] >= 1
