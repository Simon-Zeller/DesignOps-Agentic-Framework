"""Unit tests for dimension_validator — zero-size fail and valid-box pass."""
from __future__ import annotations


def test_fails_zero_size_render():
    """validate_dimensions returns passed=False for a zero-dimension bounding box."""
    from daf.tools.dimension_validator import validate_dimensions

    result = validate_dimensions({"width": 0, "height": 0}, min_width=4, min_height=4)

    assert result["passed"] is False
    assert "zero" in result["reason"].lower() or result["reason"] is not None


def test_passes_valid_bounding_box():
    """validate_dimensions returns passed=True for a sufficiently large bounding box."""
    from daf.tools.dimension_validator import validate_dimensions

    result = validate_dimensions({"width": 120, "height": 40}, min_width=4, min_height=4)

    assert result["passed"] is True
    assert result["reason"] is None
