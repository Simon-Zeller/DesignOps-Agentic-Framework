"""Tests for score_calculator.py."""
from __future__ import annotations

import pytest
from daf.tools.score_calculator import calculate_score

# Weights: test_coverage=0.25, a11y_pass_rate=0.25, token_compliance=0.20,
#          composition_depth_score=0.15, spec_completeness=0.15


def test_full_subscores_produce_correct_composite():
    sub_scores = {
        "test_coverage": 0.95,
        "a11y_pass_rate": 1.0,
        "token_compliance": 1.0,
        "composition_depth_score": 1.0,
        "spec_completeness": 1.0,
    }
    result = calculate_score(sub_scores)
    # (0.95*0.25 + 1.0*0.25 + 1.0*0.20 + 1.0*0.15 + 1.0*0.15) * 100 = 98.75
    assert result["composite"] == pytest.approx(98.75)
    assert "sub_scores" in result


def test_missing_coverage_defaults_to_zero_with_flag():
    sub_scores = {
        "test_coverage": None,
        "a11y_pass_rate": 1.0,
        "token_compliance": 1.0,
        "composition_depth_score": 1.0,
        "spec_completeness": 1.0,
    }
    result = calculate_score(sub_scores)
    # test_coverage defaults to 0.0
    # (0*0.25 + 1.0*0.25 + 1.0*0.20 + 1.0*0.15 + 1.0*0.15) * 100 = 75.0
    assert result["composite"] == pytest.approx(75.0)
    assert result.get("coverage_unavailable") is True


def test_formula_is_deterministic():
    sub_scores = {
        "test_coverage": 0.8,
        "a11y_pass_rate": 0.9,
        "token_compliance": 0.7,
        "composition_depth_score": 0.85,
        "spec_completeness": 0.95,
    }
    result1 = calculate_score(sub_scores)
    result2 = calculate_score(sub_scores)
    assert result1["composite"] == result2["composite"]


def test_all_zero_sub_scores():
    sub_scores = {
        "test_coverage": 0.0,
        "a11y_pass_rate": 0.0,
        "token_compliance": 0.0,
        "composition_depth_score": 0.0,
        "spec_completeness": 0.0,
    }
    result = calculate_score(sub_scores)
    assert result["composite"] == pytest.approx(0.0)
