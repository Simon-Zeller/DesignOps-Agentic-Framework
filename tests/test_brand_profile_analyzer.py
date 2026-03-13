"""Tests for brand_profile_analyzer.analyze_brand_profile."""
from daf.tools.brand_profile_analyzer import analyze_brand_profile


def test_extracts_archetype():
    result = analyze_brand_profile({"archetype": "vibrant", "a11y_level": "AA"})
    assert result["archetype"] == "vibrant"


def test_extracts_a11y_level():
    result = analyze_brand_profile({"archetype": "minimal", "a11y_level": "AAA"})
    assert result["a11y_level"] == "AAA"


def test_handles_missing_archetype():
    result = analyze_brand_profile({"a11y_level": "AA"})
    assert result["archetype"] == "unspecified"


def test_handles_empty_profile():
    result = analyze_brand_profile({})
    assert result["archetype"] == "unspecified"
    assert result["a11y_level"] == "AA"  # default
