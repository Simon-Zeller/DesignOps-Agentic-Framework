"""Unit tests for layout_analyzer — flexbox extraction and default-layout fallback."""
from __future__ import annotations


def test_extracts_flexbox_layout_model():
    """A spec with explicit flex layout returns the correct model dict."""
    from daf.tools.layout_analyzer import extract_layout

    spec = {"layout": {"type": "flex", "direction": "row", "align": "center"}}
    result = extract_layout(spec)

    assert result["model"] == "flex"
    assert result["direction"] == "row"
    assert result["align"] == "center"


def test_defaults_to_flex_when_layout_absent():
    """A spec with no layout field returns default flex layout."""
    from daf.tools.layout_analyzer import extract_layout

    spec = {"component": "Box"}
    result = extract_layout(spec)

    assert result["model"] == "flex"
    assert result["direction"] == "row"
    assert result["align"] == "stretch"
