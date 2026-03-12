"""Tests for the token compilation strategy (p05).

Validates the StyleDictionaryCompiler tool — per-theme CSS file generation,
CSS class-scoped selectors, multi-brand compilation, and brand guard.
"""
from __future__ import annotations

import re

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_semantic_tokens():
    """Minimal semantic token dict in nested DTCG format with com.daf.themes."""
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
            },
            "text": {
                "default": {
                    "$type": "color",
                    "$value": "{color.neutral.950}",
                    "$description": "Default text",
                    "$extensions": {
                        "com.daf.themes": {
                            "light": "{color.neutral.950}",
                            "dark": "{color.neutral.50}",
                        }
                    },
                }
            },
        }
    }


@pytest.fixture
def global_tokens():
    return {
        "color.neutral.50": "#F5F5F5",
        "color.neutral.900": "#1A1A1A",
        "color.neutral.950": "#0A0A0A",
        "color.neutral.0d0d0d": "#0d0d0d",
    }


@pytest.fixture
def brand_a_override():
    """Brand A override: only overrides surface background."""
    return {
        "color": {
            "background": {
                "surface": {
                    "$type": "color",
                    "$value": "{color.neutral.900}",
                    "$description": "Brand A dark surface",
                    "$extensions": {
                        "com.daf.themes": {
                            "light": "{color.neutral.900}",
                            "dark": "{color.neutral.950}",
                        }
                    },
                }
            }
        }
    }


# ---------------------------------------------------------------------------
# Tests — per-theme file generation
# ---------------------------------------------------------------------------

def test_two_theme_profile_produces_correct_files(tmp_path, base_semantic_tokens, global_tokens):
    """Two-theme profile produces variables.css, variables-light.css, variables-dark.css."""
    from daf.tools.style_dictionary_compiler import StyleDictionaryCompiler

    compiler = StyleDictionaryCompiler()
    written = compiler._run(
        semantic_tokens=base_semantic_tokens,
        global_tokens=global_tokens,
        theme_modes=["light", "dark"],
        default_theme="light",
        archetype="enterprise-b2b",
        brands=[],
        output_dir=str(tmp_path),
    )
    written_names = {p.split("/")[-1] for p in written}
    assert "variables.css" in written_names
    assert "variables-light.css" in written_names
    assert "variables-dark.css" in written_names


def test_default_variables_css_uses_root_selector(tmp_path, base_semantic_tokens, global_tokens):
    """variables.css (default theme) uses :root { } selector."""
    from daf.tools.style_dictionary_compiler import StyleDictionaryCompiler

    compiler = StyleDictionaryCompiler()
    written = compiler._run(
        semantic_tokens=base_semantic_tokens,
        global_tokens=global_tokens,
        theme_modes=["light", "dark"],
        default_theme="light",
        archetype="enterprise-b2b",
        brands=[],
        output_dir=str(tmp_path),
    )
    variables_path = next(p for p in written if p.endswith("variables.css"))
    with open(variables_path) as f:
        content = f.read()
    assert ":root {" in content or ":root{" in content, (
        f"variables.css must use :root selector, got:\n{content}"
    )


def test_dark_theme_file_uses_class_selector(tmp_path, base_semantic_tokens, global_tokens):
    """variables-dark.css uses .theme-dark { } selector."""
    from daf.tools.style_dictionary_compiler import StyleDictionaryCompiler

    compiler = StyleDictionaryCompiler()
    written = compiler._run(
        semantic_tokens=base_semantic_tokens,
        global_tokens=global_tokens,
        theme_modes=["light", "dark"],
        default_theme="light",
        archetype="enterprise-b2b",
        brands=[],
        output_dir=str(tmp_path),
    )
    dark_path = next(p for p in written if p.endswith("variables-dark.css"))
    with open(dark_path) as f:
        content = f.read()
    assert ".theme-dark {" in content or ".theme-dark{" in content, (
        f"variables-dark.css must use .theme-dark selector, got:\n{content}"
    )


def test_theme_files_have_identical_property_names(tmp_path, base_semantic_tokens, global_tokens):
    """All theme CSS files have the same set of custom property names."""
    from daf.tools.style_dictionary_compiler import StyleDictionaryCompiler

    compiler = StyleDictionaryCompiler()
    written = compiler._run(
        semantic_tokens=base_semantic_tokens,
        global_tokens=global_tokens,
        theme_modes=["light", "dark"],
        default_theme="light",
        archetype="enterprise-b2b",
        brands=[],
        output_dir=str(tmp_path),
    )
    prop_re = re.compile(r"(--[\w-]+)\s*:")

    def get_props(path):
        with open(path) as f:
            return set(prop_re.findall(f.read()))

    light_path = next(p for p in written if p.endswith("variables-light.css"))
    dark_path = next(p for p in written if p.endswith("variables-dark.css"))

    light_props = get_props(light_path)
    dark_props = get_props(dark_path)

    assert light_props == dark_props, (
        f"Theme files must have identical property names.\n"
        f"Only in light: {light_props - dark_props}\n"
        f"Only in dark: {dark_props - light_props}"
    )


def test_brand_compilation_uses_compound_selector(
    tmp_path, base_semantic_tokens, global_tokens, brand_a_override
):
    """Multi-brand compilation produces compound .theme-dark.brand-a selector."""
    from daf.tools.style_dictionary_compiler import StyleDictionaryCompiler

    compiler = StyleDictionaryCompiler()
    written = compiler._run(
        semantic_tokens=base_semantic_tokens,
        global_tokens=global_tokens,
        theme_modes=["light", "dark"],
        default_theme="light",
        archetype="multi-brand",
        brands=[{"name": "brand-a", "tokens": brand_a_override}],
        output_dir=str(tmp_path),
    )
    # Should produce a brand-a/variables-dark.css
    brand_dark = next(
        (p for p in written if "brand-a" in p and p.endswith("variables-dark.css")),
        None,
    )
    assert brand_dark is not None, (
        f"Expected brand-a/variables-dark.css in output, got: {written}"
    )
    with open(brand_dark) as f:
        content = f.read()
    assert ".theme-dark.brand-a" in content, (
        f"Brand dark file must use .theme-dark.brand-a selector, got:\n{content}"
    )


def test_non_multi_brand_skips_brand_compilation(tmp_path, base_semantic_tokens, global_tokens):
    """Non-multi-brand archetype does not create brand subdirectories."""
    from daf.tools.style_dictionary_compiler import StyleDictionaryCompiler

    compiler = StyleDictionaryCompiler()
    written = compiler._run(
        semantic_tokens=base_semantic_tokens,
        global_tokens=global_tokens,
        theme_modes=["light", "dark"],
        default_theme="light",
        archetype="enterprise-b2b",  # not multi-brand
        brands=[{"name": "brand-a", "tokens": {}}],  # brands provided but archetype check should skip
        output_dir=str(tmp_path),
    )
    brand_files = [p for p in written if "brand-a" in p]
    assert not brand_files, (
        f"Non-multi-brand archetype should produce no brand files, got: {brand_files}"
    )
