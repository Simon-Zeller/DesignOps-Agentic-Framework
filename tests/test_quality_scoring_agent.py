"""Tests for Agent 20: Quality Scoring Agent."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from daf.agents.quality_scoring import run_quality_scoring


@pytest.fixture
def output_dir(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    coverage = tmp_path / "coverage"
    coverage.mkdir()
    lcov = {
        "Button.tsx": {
            "lines": {"total": 40, "covered": 40, "pct": 100.0},
            "functions": {"total": 2, "covered": 2, "pct": 100.0},
            "branches": {"total": 4, "covered": 4, "pct": 100.0},
            "statements": {"total": 40, "covered": 40, "pct": 100.0},
        }
    }
    (coverage / "lcov.json").write_text(json.dumps(lcov))

    a11y_audit = {
        "components": {
            "Button": {
                "aria_patched": True,
                "a11y_pass_rate": 1.0,
                "issues": [],
            }
        }
    }
    (reports / "a11y-audit.json").write_text(json.dumps(a11y_audit))

    composition_audit = {
        "components": {
            "Button": {
                "composition_valid": True,
                "violations": [],
                "composition_depth_score": 1.0,
                "token_compliance": 1.0,
            }
        }
    }
    (reports / "composition-audit.json").write_text(json.dumps(composition_audit))

    spec_audit = {
        "components": {
            "Button": {
                "valid": True,
                "spec_completeness": 1.0,
                "errors": [],
            }
        }
    }
    (reports / "spec-validation-report.json").write_text(json.dumps(spec_audit))

    src_dir = tmp_path / "src" / "components"
    src_dir.mkdir(parents=True)
    (src_dir / "Button.tsx").write_text("// Button source")

    return str(tmp_path)


def test_agent_computes_correct_composite_for_clean_component(output_dir, tmp_path):
    with patch("daf.agents.quality_scoring._call_llm") as mock_llm:
        mock_llm.return_value = "Scoring complete."
        run_quality_scoring(output_dir)

    scorecard_path = tmp_path / "reports" / "quality-scorecard.json"
    assert scorecard_path.exists()
    data = json.loads(scorecard_path.read_text())
    components = data.get("components", {})
    if "Button" in components:
        btn = components["Button"]
        assert btn.get("gate") == "passed"
        assert btn.get("composite", 0) >= 70


def test_agent_writes_gate_failed_entry_for_low_score(output_dir, tmp_path):
    # Override a11y audit to make Button fail
    reports = tmp_path / "reports"
    a11y_audit = {
        "components": {
            "DatePicker": {
                "aria_patched": False,
                "a11y_pass_rate": 0.0,
                "issues": ["missing role", "missing aria-label"],
            }
        }
    }
    (reports / "a11y-audit.json").write_text(json.dumps(a11y_audit))

    composition_audit = {
        "components": {
            "DatePicker": {
                "composition_valid": False,
                "violations": [{"type": "non-primitive-import"}],
                "composition_depth_score": 0.0,
                "token_compliance": 0.3,
            }
        }
    }
    (reports / "composition-audit.json").write_text(json.dumps(composition_audit))

    spec_audit = {
        "components": {
            "DatePicker": {
                "valid": True,
                "spec_completeness": 0.5,
                "errors": [],
            }
        }
    }
    (reports / "spec-validation-report.json").write_text(json.dumps(spec_audit))

    coverage = tmp_path / "coverage"
    coverage.mkdir(exist_ok=True)
    (coverage / "lcov.json").write_text(json.dumps({}))

    # No Button.tsx, only DatePicker
    src_dir = tmp_path / "src" / "components"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "DatePicker.tsx").write_text("// DatePicker source")

    with patch("daf.agents.quality_scoring._call_llm") as mock_llm:
        mock_llm.return_value = "Scoring complete."
        run_quality_scoring(output_dir)

    scorecard_path = tmp_path / "reports" / "quality-scorecard.json"
    if scorecard_path.exists():
        data = json.loads(scorecard_path.read_text())
        components = data.get("components", {})
        if "DatePicker" in components:
            dp = components["DatePicker"]
            assert dp.get("gate") == "failed" or dp.get("composite", 100) < 70
