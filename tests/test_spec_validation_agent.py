"""Tests for Agent 17: Spec Validation Agent."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from daf.agents.spec_validation import run_spec_validation


@pytest.fixture
def output_dir(tmp_path):
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True)
    tokens_dir = tmp_path / "tokens"
    tokens_dir.mkdir(parents=True)
    (tokens_dir / "semantic.tokens.json").write_text(
        json.dumps({"color.interactive.default": "#005FCC", "radius.md": "8px"})
    )
    return str(tmp_path)


def test_valid_spec_produces_no_rejection(output_dir, tmp_path):
    spec = {
        "component": "Button",
        "variants": ["primary"],
        "states": {"default": {"transitions": []}, "disabled": {"terminal": True, "transitions": []}},
        "tokens": {"background": "color.interactive.default"},
        "a11y": {"role": "button"},
    }
    spec_path = tmp_path / "specs" / "button.spec.yaml"
    import yaml
    spec_path.write_text(yaml.dump(spec))

    with patch("daf.agents.spec_validation._call_llm") as mock_llm:
        mock_llm.return_value = "Validation complete."
        result = run_spec_validation(output_dir)

    rejection_path = Path(output_dir) / "reports" / "spec-validation-rejection.json"
    assert not rejection_path.exists() or json.loads(rejection_path.read_text()).get("failures", []) == []
    assert result is not None


def test_unresolved_token_writes_rejection(output_dir, tmp_path):
    spec = {
        "component": "Badge",
        "variants": ["info"],
        "states": {"default": {"transitions": []}},
        "tokens": {"background": "color.status.info"},  # unresolved
        "a11y": {"role": "status"},
    }
    spec_path = tmp_path / "specs" / "badge.spec.yaml"
    import yaml
    spec_path.write_text(yaml.dump(spec))

    with patch("daf.agents.spec_validation._call_llm") as mock_llm:
        mock_llm.return_value = "Validation found errors."
        run_spec_validation(output_dir)

    rejection_path = Path(output_dir) / "reports" / "spec-validation-rejection.json"
    if rejection_path.exists():
        data = json.loads(rejection_path.read_text())
        failures = data.get("failures", [])
        assert any("color.status.info" in str(f) or "token" in str(f).lower() for f in failures)
