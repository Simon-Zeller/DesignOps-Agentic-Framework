"""Unit tests for confidence_scorer — perfect score, Playwright-excluded, low-confidence flag."""
from __future__ import annotations


def test_perfect_score_for_fully_passing_component():
    """All sub-scores at 1.0 with render_available True returns 100."""
    from daf.tools.confidence_scorer import compute_confidence

    scores = {
        "spec_completeness": 1.0,
        "lint_pass": 1.0,
        "variant_coverage": 1.0,
        "render_pass": 1.0,
        "compilation_pass": 1.0,
        "render_available": True,
    }
    result = compute_confidence(scores)
    assert (result if isinstance(result, int) else result["score"]) == 100


def test_excludes_render_subscore_when_playwright_unavailable():
    """When render_available is False, render weight is excluded; perfect other scores = 100."""
    from daf.tools.confidence_scorer import compute_confidence

    scores = {
        "spec_completeness": 1.0,
        "lint_pass": 1.0,
        "variant_coverage": 1.0,
        "render_pass": 0.0,  # would lower score if counted
        "compilation_pass": 1.0,
        "render_available": False,
    }
    result = compute_confidence(scores)
    assert (result if isinstance(result, int) else result["score"]) == 100


def test_low_confidence_flag_set_below_60():
    """A total score below 60 sets low_confidence=True."""
    from daf.tools.confidence_scorer import compute_confidence

    scores = {
        "spec_completeness": 0.3,
        "lint_pass": 0.2,
        "variant_coverage": 0.1,
        "render_pass": 0.3,
        "compilation_pass": 0.2,
        "render_available": True,
    }
    result = compute_confidence(scores)
    # result should be a dict when score < 60
    if isinstance(result, dict):
        assert result["low_confidence"] is True
        assert result["score"] < 60
    else:
        assert result < 60


def test_all_zero_boundary():
    """All zeros with render_available True returns a score of 0."""
    from daf.tools.confidence_scorer import compute_confidence

    scores = {
        "spec_completeness": 0.0,
        "lint_pass": 0.0,
        "variant_coverage": 0.0,
        "render_pass": 0.0,
        "compilation_pass": 0.0,
        "render_available": True,
    }
    result = compute_confidence(scores)
    assert (result if isinstance(result, int) else result["score"]) == 0
