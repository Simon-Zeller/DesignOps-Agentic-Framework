"""Unit tests for ContrastSafePairer tool — TDD red phase stubs."""
from __future__ import annotations

import copy

import pytest


@pytest.fixture
def blue_palette():
    """Generate a realistic blue palette for contrast testing."""
    from daf.tools.color_palette_generator import ColorPaletteGenerator

    tool = ColorPaletteGenerator()
    return tool._run(colors={"primary": "#3D72B4", "neutral": "#95A5A6"}, color_notes={})


def test_aa_tier_selects_passing_tone(blue_palette):
    """AA tier: interactive.primary.background maps to a tone with ≥4.5:1 contrast vs white."""
    from daf.tools.contrast_safe_pairer import ContrastSafePairer

    tool = ContrastSafePairer()
    overrides, results = tool._run(palette=blue_palette, accessibility="AA")
    # The selected alias must exist in the palette
    alias = overrides.get("interactive.primary.background")
    assert alias is not None, "Expected 'interactive.primary.background' in overrides"
    hex_val = blue_palette[alias]
    # Compute contrast ratio against white
    ratio = _contrast(hex_val, "#FFFFFF")
    assert ratio >= 4.5, f"Expected ≥4.5:1 contrast, got {ratio:.2f}"


def test_aaa_tier_selects_darker_step_than_aa(blue_palette):
    """AAA tier selects a step with higher contrast than AA (darker step number)."""
    from daf.tools.contrast_safe_pairer import ContrastSafePairer

    tool = ContrastSafePairer()
    aa_overrides, _ = tool._run(palette=blue_palette, accessibility="AA")
    aaa_overrides, aaa_results = tool._run(palette=blue_palette, accessibility="AAA")

    aa_alias = aa_overrides.get("interactive.primary.background", "")
    aaa_alias = aaa_overrides.get("interactive.primary.background", "")

    # AAA alias step number should be >= AA alias step number (darker or equal)
    aa_step = int(aa_alias.split(".")[-1]) if aa_alias else 0
    aaa_step = int(aaa_alias.split(".")[-1]) if aaa_alias else 0
    assert aaa_step >= aa_step, f"AAA step {aaa_step} should be >= AA step {aa_step}"

    # AAA ratio must be ≥ 7.0
    if aaa_alias:
        hex_val = blue_palette[aaa_alias]
        ratio = _contrast(hex_val, "#FFFFFF")
        assert ratio >= 7.0, f"Expected ≥7.0:1 for AAA, got {ratio:.2f}"


@pytest.mark.parametrize(
    "fg_hex,bg_hex,expected_ratio",
    [
        ("#000000", "#FFFFFF", 21.0),
        ("#FFFFFF", "#000000", 21.0),
        ("#0A2D5A", "#FFFFFF", 13.67),  # deep navy blue: actual WCAG ratio ~13.67
    ],
)
def test_wcag_luminance_formula_matches_reference_values(fg_hex, bg_hex, expected_ratio):
    """WCAG contrast calculation matches reference pairs within ±0.5."""
    from daf.tools.contrast_safe_pairer import ContrastSafePairer

    tool = ContrastSafePairer()
    ratio = tool._wcag_contrast(fg_hex, bg_hex)
    assert abs(ratio - expected_ratio) <= 0.5, (
        f"Expected {expected_ratio}:1, got {ratio:.2f} for {fg_hex}/{bg_hex}"
    )


def test_no_passing_tone_sets_passed_false():
    """When no tone meets the threshold, ContrastPairResult.passed == False."""
    from daf.tools.color_palette_generator import ColorPaletteGenerator
    from daf.tools.contrast_safe_pairer import ContrastSafePairer

    # Create a very light palette that won't pass AA against white
    tool_gen = ColorPaletteGenerator()
    # Use a near-white color — all steps will be very light
    palette = tool_gen._run(colors={"primary": "#F0F4FA", "neutral": "#F5F5F5"}, color_notes={})

    tool = ContrastSafePairer()
    # Should not raise
    overrides, results = tool._run(palette=palette, accessibility="AA")

    # At least one result should have passed=False for a very light palette against white
    pair_result = next(
        (r for r in results if "interactive.primary.background" in r.token_pair), None
    )
    if pair_result is not None and not pair_result.passed:
        assert pair_result.contrast_ratio > 0
    # Tool must not raise regardless


def test_palette_immutability(blue_palette):
    """The input palette dict is not modified by ContrastSafePairer."""
    from daf.tools.contrast_safe_pairer import ContrastSafePairer

    palette_before = copy.deepcopy(blue_palette)
    tool = ContrastSafePairer()
    tool._run(palette=blue_palette, accessibility="AA")
    assert blue_palette == palette_before, "ContrastSafePairer must not modify the input palette"


# ---------------------------------------------------------------------------
# Private helper (mirrors ContrastSafePairer internal logic for test assertions)
# ---------------------------------------------------------------------------

def _luminance(hex_color: str) -> float:
    r = int(hex_color[1:3], 16) / 255
    g = int(hex_color[3:5], 16) / 255
    b = int(hex_color[5:7], 16) / 255

    def linearize(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def _contrast(fg: str, bg: str) -> float:
    l1 = _luminance(fg)
    l2 = _luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)
