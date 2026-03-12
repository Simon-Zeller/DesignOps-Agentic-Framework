"""Unit tests for ModularScaleCalculator tool — TDD red phase stubs."""
from __future__ import annotations

import pytest


@pytest.fixture
def standard_scale_result():
    """Run ModularScaleCalculator with a standard enterprise config."""
    from daf.tools.modular_scale_calculator import ModularScaleCalculator

    tool = ModularScaleCalculator()
    return tool._run(
        typography={"baseSize": 16, "scaleRatio": 1.25},
        spacing={"baseUnit": 4, "density": "default"},
        archetype="enterprise-b2b",
    )


def test_typography_step0_equals_base_size(standard_scale_result):
    """scale.font-size.base == '16px' when baseSize=16."""
    result = standard_scale_result
    assert result["scale.font-size.base"] == "16px"


def test_typography_lg_step_is_approximately_20px(standard_scale_result):
    """scale.font-size.lg ≈ 20px (16 × 1.25^1), within ±1px rounding."""
    result = standard_scale_result
    lg_val = result["scale.font-size.lg"]
    px_num = float(lg_val.replace("px", ""))
    assert abs(px_num - 20.0) <= 1.0, f"Expected ~20px, got {lg_val}"


def test_spacing_step4_equals_4x_base_unit(standard_scale_result):
    """scale.spacing.4 == 16px (4 × 4px base unit, default density)."""
    assert standard_scale_result["scale.spacing.4"] == "16px"


def test_spacing_step8_equals_8x_base_unit(standard_scale_result):
    """scale.spacing.8 == 32px (8 × 4px base unit, default density)."""
    assert standard_scale_result["scale.spacing.8"] == "32px"


@pytest.mark.parametrize("step", [2, 4, 8, 12])
def test_compact_density_reduces_spacing_by_75_percent(step):
    """Compact density produces ~0.75× the default-density value for same step."""
    from daf.tools.modular_scale_calculator import ModularScaleCalculator

    tool = ModularScaleCalculator()
    default_result = tool._run(
        typography={"baseSize": 16, "scaleRatio": 1.25},
        spacing={"baseUnit": 8, "density": "default"},
        archetype="enterprise-b2b",
    )
    compact_result = tool._run(
        typography={"baseSize": 16, "scaleRatio": 1.25},
        spacing={"baseUnit": 8, "density": "compact"},
        archetype="enterprise-b2b",
    )
    key = f"scale.spacing.{step}"
    default_px = float(default_result[key].replace("px", ""))
    compact_px = float(compact_result[key].replace("px", ""))
    ratio = compact_px / default_px
    assert abs(ratio - 0.75) <= 0.05, f"Expected 0.75× at step {step}, got {ratio:.3f}"


@pytest.mark.parametrize(
    "archetype",
    ["enterprise-b2b", "consumer-b2c", "marketplace", "creative-studio", "multi-brand"],
)
def test_archetype_defaults_fallback_produces_complete_scales(archetype):
    """When typography=None, archetype defaults fill in and produce valid scales."""
    from daf.tools.modular_scale_calculator import ModularScaleCalculator

    tool = ModularScaleCalculator()
    result = tool._run(typography=None, spacing=None, archetype=archetype)
    # Must contain font-size and spacing keys
    font_keys = [k for k in result if k.startswith("scale.font-size.")]
    spacing_keys = [k for k in result if k.startswith("scale.spacing.")]
    assert len(font_keys) > 0, f"No font-size keys for archetype={archetype}"
    assert len(spacing_keys) > 0, f"No spacing keys for archetype={archetype}"


def test_all_required_scale_categories_are_produced(standard_scale_result):
    """Result contains all 7 expected scale categories."""
    result = standard_scale_result
    expected_prefixes = [
        "scale.font-size.",
        "scale.spacing.",
        "scale.elevation.",
        "scale.radius.",
        "scale.opacity.",
        "scale.duration.",
        "scale.easing.",
    ]
    for prefix in expected_prefixes:
        matching = [k for k in result if k.startswith(prefix)]
        assert len(matching) > 0, f"Missing category: {prefix}"


def test_total_token_count_matches_expected_steps(standard_scale_result):
    """16 font + 12 spacing + 6 elevation + 6 radius + 10 opacity + 8 duration + 5 easing = 63."""
    result = standard_scale_result
    assert len(result) == 63


def test_spacious_density_increases_spacing():
    """Spacious density produces ~1.33× the default-density value."""
    from daf.tools.modular_scale_calculator import ModularScaleCalculator

    tool = ModularScaleCalculator()
    default_result = tool._run(
        typography={"baseSize": 16, "scaleRatio": 1.25},
        spacing={"baseUnit": 8, "density": "default"},
        archetype="enterprise-b2b",
    )
    spacious_result = tool._run(
        typography={"baseSize": 16, "scaleRatio": 1.25},
        spacing={"baseUnit": 8, "density": "spacious"},
        archetype="enterprise-b2b",
    )
    key = "scale.spacing.4"
    default_px = float(default_result[key].replace("px", ""))
    spacious_px = float(spacious_result[key].replace("px", ""))
    ratio = spacious_px / default_px
    assert abs(ratio - 1.33) <= 0.05, f"Expected 1.33× at step 4, got {ratio:.3f}"
