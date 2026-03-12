"""Unit tests for WC3DTCGFormatter tool — TDD red phase stubs."""
from __future__ import annotations

import json
import re

import pytest


@pytest.fixture
def sample_global_palette():
    """A minimal global palette fixture."""
    return {
        "color.primary.50": "#EBF2FB",
        "color.primary.500": "#3D72B4",
        "color.primary.700": "#2A5080",
        "color.primary.900": "#142840",
        "color.neutral.50": "#F5F5F5",
        "color.neutral.950": "#0A0A0A",
    }


@pytest.fixture
def sample_scale_tokens():
    """A minimal scale token dict."""
    return {
        "scale.font-size.base": "16px",
        "scale.font-size.lg": "20px",
        "scale.spacing.4": "16px",
        "scale.radius.md": "6px",
        "scale.elevation.2": "0 2px 4px rgba(0,0,0,0.12)",
        "scale.opacity.80": "80%",
        "scale.duration.200": "200ms",
        "scale.easing.ease-out": "cubic-bezier(0, 0, 0.2, 1)",
    }


@pytest.fixture
def sample_semantic_overrides():
    """Valid semantic overrides referencing global palette keys."""
    return {
        "interactive.primary.background": "color.primary.700",
        "text.default": "color.neutral.950",
        "surface.default": "color.neutral.50",
        "text.inverse": "color.neutral.50",
    }


@pytest.fixture
def formatter_output(tmp_path, sample_global_palette, sample_scale_tokens, sample_semantic_overrides):
    """Run the formatter and return (written_files, output_dir)."""
    from daf.tools.dtcg_formatter import WC3DTCGFormatter

    tool = WC3DTCGFormatter()
    written = tool._run(
        global_palette=sample_global_palette,
        scale_tokens=sample_scale_tokens,
        semantic_overrides=sample_semantic_overrides,
        component_overrides={},
        themes=[],
        brands={},
        output_dir=str(tmp_path),
    )
    return written, tmp_path


def test_global_tier_has_no_reference_strings(formatter_output):
    """base.tokens.json must not contain any {…} reference values."""
    written, output_dir = formatter_output
    base_path = next(p for p in written if p.endswith("base.tokens.json"))
    with open(base_path) as f:
        content = f.read()
    data = json.loads(content)
    _assert_no_references_in_values(data)


def test_semantic_tier_has_only_reference_strings(formatter_output):
    """semantic.tokens.json color $value fields must all be {…} references."""
    written, output_dir = formatter_output
    semantic_path = next(p for p in written if p.endswith("semantic.tokens.json"))
    with open(semantic_path) as f:
        data = json.load(f)
    _assert_all_color_values_are_references(data)


def test_every_token_has_required_dtcg_fields(formatter_output):
    """All three files: every leaf token must have $value, $type, $description."""
    written, output_dir = formatter_output
    for path in written:
        with open(path) as f:
            data = json.load(f)
        _assert_every_leaf_has_dtcg_fields(data, path)


def test_self_check_raises_value_error_on_broken_reference(tmp_path, sample_global_palette, sample_scale_tokens):
    """Typo in semantic alias raises ValueError before any file is written."""
    from daf.tools.dtcg_formatter import WC3DTCGFormatter

    broken_overrides = {
        "interactive.primary.background": "color.priary.700",  # typo: priary
    }
    tool = WC3DTCGFormatter()
    with pytest.raises(ValueError, match=r"color\.priary\.700"):
        tool._run(
            global_palette=sample_global_palette,
            scale_tokens=sample_scale_tokens,
            semantic_overrides=broken_overrides,
            component_overrides={},
            themes=[],
            brands={},
            output_dir=str(tmp_path),
        )
    # No files should have been written
    tokens_dir = tmp_path / "tokens"
    assert not tokens_dir.exists() or not any(tokens_dir.iterdir())


def test_self_check_raises_value_error_on_missing_step(tmp_path, sample_global_palette, sample_scale_tokens):
    """Reference to a non-existent step raises ValueError."""
    from daf.tools.dtcg_formatter import WC3DTCGFormatter

    broken_overrides = {
        "interactive.primary.background": "color.primary.999",  # step 999 doesn't exist
    }
    tool = WC3DTCGFormatter()
    with pytest.raises(ValueError, match=r"color\.primary\.999"):
        tool._run(
            global_palette=sample_global_palette,
            scale_tokens=sample_scale_tokens,
            semantic_overrides=broken_overrides,
            component_overrides={},
            themes=[],
            brands={},
            output_dir=str(tmp_path),
        )


def test_multi_theme_extensions_block(tmp_path, sample_global_palette, sample_scale_tokens):
    """Multi-theme profiles include $extensions.themes on semantic tokens."""
    from daf.tools.dtcg_formatter import WC3DTCGFormatter

    theme_overrides = {
        "interactive.primary.background": "color.primary.700",
        "surface.default": "color.neutral.50",
        "text.default": "color.neutral.950",
        "text.inverse": "color.neutral.50",
    }
    tool = WC3DTCGFormatter()
    written = tool._run(
        global_palette=sample_global_palette,
        scale_tokens=sample_scale_tokens,
        semantic_overrides=theme_overrides,
        component_overrides={},
        themes=["light", "dark"],
        brands={},
        output_dir=str(tmp_path),
    )
    semantic_path = next(p for p in written if p.endswith("semantic.tokens.json"))
    with open(semantic_path) as f:
        data = json.load(f)
    # At least one token must have $extensions.com.daf.themes
    found = _find_extensions_com_daf_themes(data)
    assert found, "Expected at least one token with $extensions.com.daf.themes in semantic tier"


def test_tokens_directory_created_if_absent(tmp_path, sample_global_palette, sample_scale_tokens, sample_semantic_overrides):
    """tokens/ sub-directory is created inside output_dir if not present."""
    from daf.tools.dtcg_formatter import WC3DTCGFormatter

    nested_dir = tmp_path / "project"
    nested_dir.mkdir()  # project/ exists, but project/tokens/ does not

    tool = WC3DTCGFormatter()
    written = tool._run(
        global_palette=sample_global_palette,
        scale_tokens=sample_scale_tokens,
        semantic_overrides=sample_semantic_overrides,
        component_overrides={},
        themes=[],
        brands={},
        output_dir=str(nested_dir),
    )
    tokens_dir = nested_dir / "tokens"
    assert tokens_dir.is_dir()
    assert len(written) >= 3


def test_multi_brand_generates_per_brand_files(tmp_path, sample_global_palette, sample_scale_tokens, sample_semantic_overrides):
    """Multi-brand profile writes tokens/brands/<name>.tokens.json for each brand."""
    from daf.tools.dtcg_formatter import WC3DTCGFormatter

    brands = {
        "brand-a": {"interactive.primary.background": "color.primary.500"},
        "brand-b": {"interactive.primary.background": "color.primary.700"},
    }
    tool = WC3DTCGFormatter()
    written = tool._run(
        global_palette=sample_global_palette,
        scale_tokens=sample_scale_tokens,
        semantic_overrides=sample_semantic_overrides,
        component_overrides={},
        themes=[],
        brands=brands,
        output_dir=str(tmp_path),
    )
    brand_paths = [p for p in written if "brands" in p]
    assert len(brand_paths) == 2
    brand_names = [p.split("/brands/")[1].replace(".tokens.json", "") for p in brand_paths]
    assert "brand-a" in brand_names
    assert "brand-b" in brand_names


def test_output_is_valid_utf8_json(formatter_output):
    """All output files are valid UTF-8 JSON."""
    written, _ = formatter_output
    for path in written:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# Helper assertions
# ---------------------------------------------------------------------------

def _assert_no_references_in_values(data: dict, path: str = "") -> None:
    """Recursively assert that no $value contains a { character."""
    for key, val in data.items():
        current_path = f"{path}.{key}" if path else key
        if key == "$value":
            assert "{" not in str(val), f"Reference found in global tier at {path}: {val}"
        elif isinstance(val, dict):
            _assert_no_references_in_values(val, current_path)


def _assert_all_color_values_are_references(data: dict, path: str = "") -> None:
    """Recursively assert that color-typed $value fields in semantic tier are references."""
    ref_pattern = re.compile(r"^\{[a-z0-9._-]+\}$")
    for key, val in data.items():
        current_path = f"{path}.{key}" if path else key
        if key == "$value" and isinstance(val, str):
            # Only assert for color-typed tokens
            if data.get("$type") == "color":
                assert ref_pattern.match(val), (
                    f"Semantic color token at {path} has non-reference value: {val}"
                )
        elif isinstance(val, dict) and not key.startswith("$"):
            _assert_all_color_values_are_references(val, current_path)


def _assert_every_leaf_has_dtcg_fields(data: dict, file_path: str, path: str = "") -> None:
    """Recursively assert every leaf token dict has $value, $type, $description."""
    if "$value" in data:
        assert "$type" in data, f"Missing $type at {path} in {file_path}"
        assert "$description" in data, f"Missing $description at {path} in {file_path}"
        return
    for key, val in data.items():
        if isinstance(val, dict) and not key.startswith("$"):
            current_path = f"{path}.{key}" if path else key
            _assert_every_leaf_has_dtcg_fields(val, file_path, current_path)


def _find_extensions_themes(data: dict) -> bool:
    """Return True if any leaf token has $extensions.themes."""
    if "$value" in data:
        ext = data.get("$extensions", {})
        if "themes" in ext:
            return True
        return False
    for key, val in data.items():
        if isinstance(val, dict) and not key.startswith("$"):
            if _find_extensions_themes(val):
                return True
    return False


# ---------------------------------------------------------------------------
# p05 — com.daf.themes namespace tests (TDD red phase)
# ---------------------------------------------------------------------------

def test_multi_theme_uses_com_daf_themes_key(tmp_path, sample_global_palette, sample_scale_tokens):
    """WC3DTCGFormatter must write $extensions.com.daf.themes, not bare $extensions.themes."""
    from daf.tools.dtcg_formatter import WC3DTCGFormatter

    theme_overrides = {
        "interactive.primary.background": "color.primary.700",
        "surface.default": "color.neutral.50",
    }
    tool = WC3DTCGFormatter()
    written = tool._run(
        global_palette=sample_global_palette,
        scale_tokens=sample_scale_tokens,
        semantic_overrides=theme_overrides,
        component_overrides={},
        themes=["light", "dark"],
        brands={},
        output_dir=str(tmp_path),
    )
    semantic_path = next(p for p in written if p.endswith("semantic.tokens.json"))
    with open(semantic_path) as f:
        data = json.load(f)

    # Must find at least one token with $extensions.com.daf.themes
    found_com_daf = _find_extensions_com_daf_themes(data)
    assert found_com_daf, "Expected $extensions.com.daf.themes key in semantic tokens"

    # Must NOT find any token with bare $extensions.themes
    found_bare = _find_extensions_bare_themes(data)
    assert not found_bare, "Found forbidden bare $extensions.themes key — must use com.daf.themes"


def test_bare_themes_key_raises_value_error(tmp_path, sample_global_palette, sample_scale_tokens):
    """WC3DTCGFormatter raises ValueError if internal logic would emit bare 'themes' key."""
    from daf.tools.dtcg_formatter import _flat_to_nested_with_themes

    # Call the internal helper directly to verify the guard raises
    with pytest.raises(ValueError, match=r"com\.daf\.themes"):
        _flat_to_nested_with_themes(
            flat_tokens={"surface.default": "color.neutral.50"},
            themes=["light", "dark"],
            _force_bare_key=True,  # trigger the guard path
        )


def _find_extensions_com_daf_themes(data: dict) -> bool:
    """Return True if any leaf token has $extensions.com.daf.themes."""
    if "$value" in data:
        ext = data.get("$extensions", {})
        return "com.daf.themes" in ext
    for key, val in data.items():
        if isinstance(val, dict) and not key.startswith("$"):
            if _find_extensions_com_daf_themes(val):
                return True
    return False


def _find_extensions_bare_themes(data: dict) -> bool:
    """Return True if any leaf token has bare $extensions.themes (wrong key)."""
    if "$value" in data:
        ext = data.get("$extensions", {})
        return "themes" in ext and "com.daf.themes" not in ext
    for key, val in data.items():
        if isinstance(val, dict) and not key.startswith("$"):
            if _find_extensions_bare_themes(val):
                return True
    return False
