"""Tests for structural profile validator (TDD red phase — §13.3 rules)."""

import pytest


def _valid_profile(**overrides):
    """Return a minimally valid brand profile dict."""
    base = {
        "name": "My Design System",
        "archetype": "enterprise-b2b",
        "colors": {
            "primary": "#1a73e8",
            "secondary": "#5f6368",
            "neutral": "#f1f3f4",
            "semantic": {
                "success": "#34a853",
                "warning": "#fbbc04",
                "error": "#ea4335",
                "info": "#4285f4",
            },
        },
        "typography": {
            "scaleRatio": 1.25,
            "baseSize": 16,
        },
        "spacing": {"density": "compact"},
        "borderRadius": "sm",
        "elevation": "subtle",
        "motion": "reduced",
        "themes": ["light", "dark"],
        "accessibility": "AA",
        "componentScope": "comprehensive",
        "breakpoints": {"sm": "640px", "md": "768px", "lg": "1024px", "xl": "1280px"},
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Valid profile
# ---------------------------------------------------------------------------


def test_valid_complete_profile_no_errors():
    from daf.validator import validate_profile

    errors = validate_profile(_valid_profile())
    assert errors == []


# ---------------------------------------------------------------------------
# Name validation
# ---------------------------------------------------------------------------


def test_missing_name_returns_error():
    from daf.validator import validate_profile

    errors = validate_profile(_valid_profile(name=""))
    assert any("name" in e for e in errors)


def test_whitespace_only_name_returns_error():
    from daf.validator import validate_profile

    errors = validate_profile(_valid_profile(name="   "))
    assert any("name" in e for e in errors)


# ---------------------------------------------------------------------------
# Archetype validation
# ---------------------------------------------------------------------------


def test_invalid_archetype_returns_error():
    from daf.validator import validate_profile

    errors = validate_profile(_valid_profile(archetype="fantasy-theme"))
    assert any("archetype" in e for e in errors)


@pytest.mark.parametrize(
    "archetype",
    ["enterprise-b2b", "consumer-b2c", "mobile-first", "multi-brand", "custom"],
)
def test_valid_archetype_no_error(archetype):
    from daf.validator import validate_profile

    errors = validate_profile(_valid_profile(archetype=archetype))
    assert not any("archetype" in e for e in errors)


# ---------------------------------------------------------------------------
# Hex color validation — primary
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_color",
    ["#GGGGGG", "#12345", "red", "rgb(255,0,0)", ""],
)
def test_invalid_primary_color_returns_error(bad_color):
    from daf.validator import validate_profile

    profile = _valid_profile()
    profile["colors"]["primary"] = bad_color
    errors = validate_profile(profile)
    assert any("colors.primary" in e for e in errors), (
        f"Expected error for colors.primary={bad_color!r}, got: {errors}"
    )


@pytest.mark.parametrize(
    "good_color",
    ["#1a73e8", "#FF0000", "#fff", "#000", "#ABC"],
)
def test_valid_primary_color_no_error(good_color):
    from daf.validator import validate_profile

    profile = _valid_profile()
    profile["colors"]["primary"] = good_color
    errors = validate_profile(profile)
    assert not any("colors.primary" in e for e in errors), (
        f"Unexpected error for colors.primary={good_color!r}: {errors}"
    )


def test_natural_language_color_passes_validation():
    from daf.validator import validate_profile

    profile = _valid_profile()
    profile["colors"]["primary"] = "a warm coral red"
    errors = validate_profile(profile)
    assert not any("colors.primary" in e for e in errors)


# ---------------------------------------------------------------------------
# Hex color validation — all colors.* sub-fields (parametrized)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field_path",
    [
        ("colors", "secondary"),
        ("colors", "neutral"),
    ],
)
def test_invalid_top_level_color_subfield_returns_error(field_path):
    from daf.validator import validate_profile

    profile = _valid_profile()
    profile[field_path[0]][field_path[1]] = "#INVALID"
    errors = validate_profile(profile)
    dotpath = ".".join(field_path)
    assert any(dotpath in e for e in errors), (
        f"Expected error for {dotpath}, got: {errors}"
    )


@pytest.mark.parametrize(
    "semantic_field",
    ["success", "warning", "error", "info"],
)
def test_invalid_semantic_color_field_returns_error(semantic_field):
    from daf.validator import validate_profile

    profile = _valid_profile()
    profile["colors"]["semantic"][semantic_field] = "#INVALID"
    errors = validate_profile(profile)
    field_path = f"colors.semantic.{semantic_field}"
    assert any(field_path in e for e in errors), (
        f"Expected error for {field_path}, got: {errors}"
    )


# ---------------------------------------------------------------------------
# Typography — scaleRatio
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ratio", [1.0, 1.25, 1.5, 2.0])
def test_valid_scale_ratio_no_error(ratio):
    from daf.validator import validate_profile

    profile = _valid_profile()
    profile["typography"]["scaleRatio"] = ratio
    errors = validate_profile(profile)
    assert not any("scaleRatio" in e for e in errors)


@pytest.mark.parametrize("ratio", [0.9, 2.1, 0.0, -1.0, 5.0])
def test_invalid_scale_ratio_returns_error(ratio):
    from daf.validator import validate_profile

    profile = _valid_profile()
    profile["typography"]["scaleRatio"] = ratio
    errors = validate_profile(profile)
    assert any("scaleRatio" in e for e in errors), (
        f"Expected scaleRatio error for {ratio}, got: {errors}"
    )


# ---------------------------------------------------------------------------
# Typography — baseSize
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("size", [8, 12, 16, 24])
def test_valid_base_size_no_error(size):
    from daf.validator import validate_profile

    profile = _valid_profile()
    profile["typography"]["baseSize"] = size
    errors = validate_profile(profile)
    assert not any("baseSize" in e for e in errors)


@pytest.mark.parametrize("size", [7, 25, 0, 100])
def test_invalid_base_size_returns_error(size):
    from daf.validator import validate_profile

    profile = _valid_profile()
    profile["typography"]["baseSize"] = size
    errors = validate_profile(profile)
    assert any("baseSize" in e for e in errors), (
        f"Expected baseSize error for {size}, got: {errors}"
    )
