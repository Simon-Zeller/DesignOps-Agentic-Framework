"""Unit tests for ColorPaletteGenerator tool — TDD red phase stubs."""
from __future__ import annotations

import pytest


@pytest.fixture
def standard_palette_result():
    """Return the result of running ColorPaletteGenerator on a standard hex color."""
    from daf.tools.color_palette_generator import ColorPaletteGenerator

    tool = ColorPaletteGenerator()
    return tool._run(colors={"primary": "#3D72B4"}, color_notes={})


def test_hex_anchor_generates_11_step_scale(standard_palette_result):
    """Step 500 equals brand hex; 11 keys total for the role."""
    result = standard_palette_result
    primary_keys = [k for k in result if k.startswith("color.primary.")]
    assert len(primary_keys) == 11
    assert result["color.primary.500"] == "#3D72B4"


def test_all_generated_values_are_valid_hex(standard_palette_result):
    """Every generated value matches #RRGGBB format."""
    import re

    hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
    for value in standard_palette_result.values():
        assert hex_pattern.match(value), f"Invalid hex: {value}"


def test_tonal_ordering_lighter_steps_have_higher_lightness(standard_palette_result):
    """Lighter steps (lower step number) have higher HSL lightness than step 500."""
    import colorsys

    def lightness(hex_color: str) -> float:
        r = int(hex_color[1:3], 16) / 255
        g = int(hex_color[3:5], 16) / 255
        b = int(hex_color[5:7], 16) / 255
        h, lightness, s = colorsys.rgb_to_hls(r, g, b)
        return lightness

    result = standard_palette_result
    steps = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]
    lightnesses = [lightness(result[f"color.primary.{step}"]) for step in steps]
    # Each step should be darker (lower lightness) than the previous
    for i in range(len(lightnesses) - 1):
        assert lightnesses[i] >= lightnesses[i + 1], (
            f"Step {steps[i]} lightness {lightnesses[i]:.3f} should be >= "
            f"step {steps[i+1]} lightness {lightnesses[i+1]:.3f}"
        )


def test_color_notes_hex_annotation_used_as_anchor():
    """Hex extracted from _color_notes becomes the step 500 anchor."""
    from daf.tools.color_palette_generator import ColorPaletteGenerator

    tool = ColorPaletteGenerator()
    result = tool._run(
        colors={"primary": "ocean blue"},
        color_notes={"colors.primary": "Interpreted as #1E6FA8 — deep professional blue"},
    )
    assert result["color.primary.500"] == "#1E6FA8"


@pytest.mark.parametrize("color_name", ["cerulean", "coral", "navy"])
def test_lookup_table_fallback_resolves_common_color_names(color_name):
    """Known color names resolve via lookup table to a valid hex without raising."""
    import re

    from daf.tools.color_palette_generator import ColorPaletteGenerator

    tool = ColorPaletteGenerator()
    result = tool._run(colors={"primary": color_name}, color_notes={})
    hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
    assert hex_pattern.match(result["color.primary.500"])


def test_absent_roles_produce_no_tokens():
    """Only roles actually present in the colors dict get tokens."""
    from daf.tools.color_palette_generator import ColorPaletteGenerator

    tool = ColorPaletteGenerator()
    result = tool._run(colors={"primary": "#FF5733"}, color_notes={})
    for key in result:
        assert key.startswith("color.primary."), f"Unexpected key: {key}"


def test_multiple_roles_get_independent_scales():
    """4 roles → 44 tokens; each role's step 500 equals its input hex."""
    from daf.tools.color_palette_generator import ColorPaletteGenerator

    tool = ColorPaletteGenerator()
    colors = {
        "primary": "#3D72B4",
        "secondary": "#2ECC71",
        "accent": "#E74C3C",
        "neutral": "#95A5A6",
    }
    result = tool._run(colors=colors, color_notes={})
    assert len(result) == 4 * 11
    for role, hex_val in colors.items():
        assert result[f"color.{role}.500"] == hex_val
