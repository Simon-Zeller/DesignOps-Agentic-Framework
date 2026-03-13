"""Tests for daf.tools.drift_reporter — classify_drift and DriftReporter tool."""
from __future__ import annotations

from daf.tools.drift_reporter import DriftReporter, classify_drift


def test_classify_drift_auto_fixable() -> None:
    """Prop in spec+code but missing from docs → auto-fixable."""
    items = [{"component": "Button", "prop": "disabled", "in_spec": True, "in_code": True, "in_docs": False}]
    result = classify_drift(items)
    assert len(result["fixable"]) == 1
    assert result["fixable"][0]["category"] == "auto-fixable"
    assert result["non_fixable"] == []


def test_classify_drift_re_run_required() -> None:
    """Prop in spec but missing from code → re-run-required."""
    items = [{"component": "Button", "prop": "variant", "in_spec": True, "in_code": False, "in_docs": False}]
    result = classify_drift(items)
    assert result["fixable"] == []
    assert len(result["non_fixable"]) == 1
    assert result["non_fixable"][0]["category"] == "re-run-required"


def test_classify_drift_review_category() -> None:
    """Prop not in spec → review category."""
    items = [{"component": "Button", "prop": "extra", "in_spec": False, "in_code": True, "in_docs": True}]
    result = classify_drift(items)
    assert result["fixable"] == []
    assert result["non_fixable"][0]["category"] == "review"


def test_classify_drift_empty() -> None:
    """Empty input returns empty lists."""
    result = classify_drift([])
    assert result == {"fixable": [], "non_fixable": []}


def test_classify_drift_mixed() -> None:
    """Mixed items are classified correctly."""
    items = [
        {"component": "A", "prop": "p1", "in_spec": True, "in_code": True, "in_docs": False},
        {"component": "A", "prop": "p2", "in_spec": True, "in_code": False, "in_docs": False},
        {"component": "A", "prop": "p3", "in_spec": False, "in_code": True, "in_docs": True},
    ]
    result = classify_drift(items)
    assert len(result["fixable"]) == 1
    assert len(result["non_fixable"]) == 2
    categories = {item["category"] for item in result["non_fixable"]}
    assert "re-run-required" in categories
    assert "review" in categories


def test_drift_reporter_tool_type() -> None:
    """DriftReporter is a BaseTool."""
    from crewai.tools import BaseTool
    assert isinstance(DriftReporter(), BaseTool)


def test_drift_reporter_tool_run() -> None:
    """DriftReporter._run delegates to classify_drift."""
    tool = DriftReporter()
    items = [{"component": "C", "prop": "x", "in_spec": True, "in_code": True, "in_docs": False}]
    result = tool._run(drift_items=items)
    assert len(result["fixable"]) == 1
    assert result["fixable"][0]["category"] == "auto-fixable"
