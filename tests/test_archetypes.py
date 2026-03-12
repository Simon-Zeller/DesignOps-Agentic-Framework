"""Tests for archetype defaults map (TDD red phase)."""

import pytest

ARCHETYPES = ["enterprise-b2b", "consumer-b2c", "mobile-first", "multi-brand", "custom"]

REQUIRED_OPTIONAL_FIELDS = [
    "colors",
    "typography",
    "spacing",
    "borderRadius",
    "elevation",
    "motion",
    "themes",
    "accessibility",
    "componentScope",
    "breakpoints",
]


def test_all_archetypes_present():
    from daf.archetypes import ARCHETYPE_DEFAULTS

    for archetype in ARCHETYPES:
        assert archetype in ARCHETYPE_DEFAULTS, f"Missing archetype: {archetype}"


@pytest.mark.parametrize("archetype", ARCHETYPES)
def test_archetype_has_all_required_optional_fields(archetype):
    from daf.archetypes import ARCHETYPE_DEFAULTS

    defaults = ARCHETYPE_DEFAULTS[archetype]
    for field in REQUIRED_OPTIONAL_FIELDS:
        assert field in defaults, f"{archetype} missing field: {field}"


@pytest.mark.parametrize("archetype", ARCHETYPES)
def test_archetype_colors_has_required_subfields(archetype):
    from daf.archetypes import ARCHETYPE_DEFAULTS

    colors = ARCHETYPE_DEFAULTS[archetype]["colors"]
    for subfield in ("primary", "secondary", "neutral"):
        assert subfield in colors, f"{archetype}.colors missing: {subfield}"
    semantic = colors.get("semantic", {})
    for subfield in ("success", "warning", "error", "info"):
        assert subfield in semantic, f"{archetype}.colors.semantic missing: {subfield}"


@pytest.mark.parametrize("archetype", ARCHETYPES)
def test_archetype_typography_has_required_subfields(archetype):
    from daf.archetypes import ARCHETYPE_DEFAULTS

    typography = ARCHETYPE_DEFAULTS[archetype]["typography"]
    assert "scaleRatio" in typography
    assert "baseSize" in typography


def test_enterprise_b2b_accessibility_is_AA():
    from daf.archetypes import ARCHETYPE_DEFAULTS

    assert ARCHETYPE_DEFAULTS["enterprise-b2b"]["accessibility"] == "AA"


def test_enterprise_b2b_component_scope_is_comprehensive():
    from daf.archetypes import ARCHETYPE_DEFAULTS

    assert ARCHETYPE_DEFAULTS["enterprise-b2b"]["componentScope"] == "comprehensive"


def test_enterprise_b2b_spacing_density():
    from daf.archetypes import ARCHETYPE_DEFAULTS

    density = ARCHETYPE_DEFAULTS["enterprise-b2b"]["spacing"]["density"]
    assert density in ("compact", "default"), f"Unexpected density: {density}"
