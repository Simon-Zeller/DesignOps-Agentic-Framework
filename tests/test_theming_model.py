"""Tests for theming model token extension validation (p05).

Validates the `validate_theme_extensions` function that enforces the
$extensions.com.daf.themes DTCG convention per the theming-model spec.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def global_tokens():
    """Minimal global token tier for reference resolution."""
    return {
        "color.neutral.50": "#F5F5F5",
        "color.neutral.100": "#EDEDED",
        "color.neutral.900": "#1A1A1A",
        "color.neutral.950": "#0A0A0A",
        "color.primary.700": "#2A5080",
    }


@pytest.fixture
def theme_modes():
    return ["light", "dark"]


@pytest.fixture
def valid_semantic_tokens():
    """Well-formed semantic token dict with com.daf.themes blocks."""
    return {
        "color": {
            "background": {
                "surface": {
                    "$type": "color",
                    "$value": "{color.neutral.50}",
                    "$description": "Surface background",
                    "$extensions": {
                        "com.daf.themes": {
                            "light": "{color.neutral.50}",
                            "dark": "{color.neutral.900}",
                        }
                    },
                }
            }
        }
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_bare_themes_key_is_fatal_error(global_tokens, theme_modes):
    """validate_theme_extensions reports fatal error for bare $extensions.themes key."""
    from daf.validator import validate_theme_extensions

    semantic_tokens = {
        "color": {
            "background": {
                "surface": {
                    "$type": "color",
                    "$value": "{color.neutral.50}",
                    "$description": "Surface background",
                    "$extensions": {
                        "themes": {  # bare key — wrong namespace
                            "light": "{color.neutral.50}",
                            "dark": "{color.neutral.900}",
                        }
                    },
                }
            }
        }
    }
    errors = validate_theme_extensions(semantic_tokens, global_tokens, theme_modes)
    assert errors, "Expected at least one fatal error for bare 'themes' key"
    fatal = [e for e in errors if e.get("severity") == "fatal"]
    assert fatal, "Expected severity=fatal for bare 'themes' key"
    assert any("com.daf.themes" in e.get("error", "") for e in fatal), (
        "Error message should reference the correct key 'com.daf.themes'"
    )


def test_raw_hex_value_in_com_daf_themes_is_fatal(global_tokens, theme_modes):
    """validate_theme_extensions reports fatal error when a com.daf.themes value is a raw hex string."""
    from daf.validator import validate_theme_extensions

    semantic_tokens = {
        "color": {
            "background": {
                "surface": {
                    "$type": "color",
                    "$value": "{color.neutral.50}",
                    "$description": "Surface background",
                    "$extensions": {
                        "com.daf.themes": {
                            "light": "{color.neutral.50}",
                            "dark": "#1A1A1A",  # raw hex — must be an alias reference
                        }
                    },
                }
            }
        }
    }
    errors = validate_theme_extensions(semantic_tokens, global_tokens, theme_modes)
    fatal = [e for e in errors if e.get("severity") == "fatal"]
    assert fatal, "Expected fatal error for raw hex value in com.daf.themes"
    assert any("dark" in e.get("error", "") or "#1A1A1A" in e.get("error", "") for e in fatal)


def test_phantom_alias_reference_is_fatal(global_tokens, theme_modes):
    """validate_theme_extensions reports fatal error when an alias reference does not exist."""
    from daf.validator import validate_theme_extensions

    semantic_tokens = {
        "color": {
            "background": {
                "surface": {
                    "$type": "color",
                    "$value": "{color.neutral.50}",
                    "$description": "Surface background",
                    "$extensions": {
                        "com.daf.themes": {
                            "light": "{color.neutral.50}",
                            "dark": "{color.neutral.99}",  # does not exist in global tier
                        }
                    },
                }
            }
        }
    }
    errors = validate_theme_extensions(semantic_tokens, global_tokens, theme_modes)
    fatal = [e for e in errors if e.get("severity") == "fatal"]
    assert fatal, "Expected fatal error for phantom alias reference"
    assert any("color.neutral.99" in e.get("error", "") for e in fatal)


def test_valid_com_daf_themes_block_has_no_errors(valid_semantic_tokens, global_tokens, theme_modes):
    """validate_theme_extensions returns no errors for a well-formed com.daf.themes block."""
    from daf.validator import validate_theme_extensions

    errors = validate_theme_extensions(valid_semantic_tokens, global_tokens, theme_modes)
    fatal = [e for e in errors if e.get("severity") == "fatal"]
    assert not fatal, f"Expected no fatal errors for valid token, got: {fatal}"
