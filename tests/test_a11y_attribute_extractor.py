"""Unit tests for a11y_attribute_extractor — ARIA role-to-attributes mapping."""
from __future__ import annotations


def test_maps_button_role_to_correct_aria_attributes():
    """A spec with a11y role: button returns the correct ARIA attrs and keyboard handlers."""
    from daf.tools.a11y_attribute_extractor import extract_a11y_attributes

    spec = {"a11y": {"role": "button"}}
    result = extract_a11y_attributes(spec)

    assert result["role"] == "button"
    assert "aria-label" in result["attrs"]
    assert "aria-disabled" in result["attrs"]
    assert "Enter" in result["keyboard"]
    assert "Space" in result["keyboard"]
