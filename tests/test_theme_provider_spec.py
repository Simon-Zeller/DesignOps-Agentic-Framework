"""Tests for ThemeProvider spec YAML generation (p05 — Agent 4).

Validates that the Primitive Spec Generator produces a ThemeProvider.spec.yaml
with the correct props, tokenBindings, and exports per the theme-provider spec.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_theme_provider_spec_yaml_is_generated(tmp_path):
    """generate_theme_provider_spec creates specs/ThemeProvider.spec.yaml."""
    from daf.tools.primitive_spec_generator import generate_theme_provider_spec

    result = generate_theme_provider_spec(output_dir=str(tmp_path))
    spec_path = tmp_path / "specs" / "ThemeProvider.spec.yaml"
    assert spec_path.exists(), (
        f"Expected specs/ThemeProvider.spec.yaml to exist at {spec_path}"
    )
    assert result == str(spec_path)


def test_theme_provider_spec_has_required_props(tmp_path):
    """ThemeProvider.spec.yaml contains all 5 required props."""
    from daf.tools.primitive_spec_generator import generate_theme_provider_spec
    import yaml

    generate_theme_provider_spec(output_dir=str(tmp_path))
    spec_path = tmp_path / "specs" / "ThemeProvider.spec.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    props = spec.get("props", {})
    required_props = {"defaultTheme", "defaultBrand", "availableThemes", "availableBrands", "children"}
    missing = required_props - set(props.keys())
    assert not missing, f"Missing required props in spec: {missing}"


def test_theme_provider_spec_has_empty_token_bindings(tmp_path):
    """ThemeProvider.spec.yaml has tokenBindings: [] (no token consumption)."""
    from daf.tools.primitive_spec_generator import generate_theme_provider_spec
    import yaml

    generate_theme_provider_spec(output_dir=str(tmp_path))
    spec_path = tmp_path / "specs" / "ThemeProvider.spec.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    assert "tokenBindings" in spec, "spec must have tokenBindings key"
    assert spec["tokenBindings"] == [], (
        f"tokenBindings must be an empty list, got: {spec['tokenBindings']}"
    )


def test_theme_provider_spec_exports_both_symbols(tmp_path):
    """ThemeProvider.spec.yaml exports: ['ThemeProvider', 'useTheme']."""
    from daf.tools.primitive_spec_generator import generate_theme_provider_spec
    import yaml

    generate_theme_provider_spec(output_dir=str(tmp_path))
    spec_path = tmp_path / "specs" / "ThemeProvider.spec.yaml"
    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    exports = spec.get("exports", [])
    assert "ThemeProvider" in exports, f"exports must include 'ThemeProvider', got: {exports}"
    assert "useTheme" in exports, f"exports must include 'useTheme', got: {exports}"
