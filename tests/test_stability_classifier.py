"""Tests for stability_classifier tool."""
from __future__ import annotations


def test_beta_classification_for_coverage_below_threshold():
    """Component with score 75, coverage 0.72 is classified as beta."""
    from daf.tools.stability_classifier import classify

    components = ["Button"]
    scorecard = {"Button": {"composite": 75.0, "coverage": 0.72}}
    config: dict = {}

    result = classify(components, scorecard, config)
    assert result["Button"] == "beta"


def test_stable_classification_for_high_score_and_coverage():
    """Component with score 85, coverage 0.85 is classified as stable."""
    from daf.tools.stability_classifier import classify

    components = ["Card"]
    scorecard = {"Card": {"composite": 85.0, "coverage": 0.85}}
    config: dict = {}

    result = classify(components, scorecard, config)
    assert result["Card"] == "stable"


def test_explicit_experimental_tag_takes_precedence():
    """Component with explicit experimental tag is classified as experimental regardless of score."""
    from daf.tools.stability_classifier import classify

    components = ["DataGrid"]
    scorecard = {"DataGrid": {"composite": 82.0, "coverage": 0.85}}
    config = {"explicit_tags": {"DataGrid": "experimental"}}

    result = classify(components, scorecard, config)
    assert result["DataGrid"] == "experimental"


def test_low_score_is_experimental():
    """Component with score below 70 is classified as experimental."""
    from daf.tools.stability_classifier import classify

    components = ["NewWidget"]
    scorecard = {"NewWidget": {"composite": 55.0, "coverage": 0.50}}
    config: dict = {}

    result = classify(components, scorecard, config)
    assert result["NewWidget"] == "experimental"
