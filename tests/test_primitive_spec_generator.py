"""Tests for generate_all_primitive_specs and PrimitiveSpecGenerator tool."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from daf.tools.primitive_spec_generator import (
    PrimitiveSpecGenerator,
    generate_all_primitive_specs,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALL_COMPONENTS = [
    "Box",
    "Stack",
    "HStack",
    "VStack",
    "Grid",
    "Text",
    "Icon",
    "Pressable",
    "Divider",
    "Spacer",
    "ThemeProvider",
]

LAYOUT_PRIMITIVES = ["Box", "Stack", "HStack", "VStack", "Grid", "ThemeProvider"]
LEAF_PRIMITIVES = ["Text", "Icon", "Divider", "Spacer"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_spec(output_dir: Path, name: str) -> dict:
    spec_path = output_dir / "specs" / f"{name}.spec.yaml"
    with open(spec_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_generate_all_primitive_specs_produces_11_files(tmp_path: Path) -> None:
    generate_all_primitive_specs(str(tmp_path))
    specs_dir = tmp_path / "specs"
    yaml_files = list(specs_dir.glob("*.spec.yaml"))
    assert len(yaml_files) == 11, f"Expected 11 files, found {len(yaml_files)}: {yaml_files}"


def test_generate_all_primitive_specs_returns_dict_with_11_keys(tmp_path: Path) -> None:
    result = generate_all_primitive_specs(str(tmp_path))
    assert isinstance(result, dict)
    assert set(result.keys()) == set(ALL_COMPONENTS), (
        f"Keys mismatch: {set(result.keys())} vs {set(ALL_COMPONENTS)}"
    )


def test_generate_all_primitive_specs_is_idempotent(tmp_path: Path) -> None:
    first = generate_all_primitive_specs(str(tmp_path))
    second = generate_all_primitive_specs(str(tmp_path))

    # No error raised; keys are the same
    assert set(first.keys()) == set(second.keys())

    # File content is unchanged
    for name in ALL_COMPONENTS:
        spec_path = tmp_path / "specs" / f"{name}.spec.yaml"
        content = spec_path.read_text(encoding="utf-8")
        assert content, f"{name}.spec.yaml is empty"


@pytest.mark.parametrize("component", ALL_COMPONENTS)
def test_each_spec_has_required_fields(tmp_path: Path, component: str) -> None:
    generate_all_primitive_specs(str(tmp_path))
    spec = _load_spec(tmp_path, component)
    for field in ("component", "description", "props", "tokenBindings", "compositionRules", "a11yRequirements"):
        assert field in spec, f"{component}.spec.yaml missing field '{field}'"


@pytest.mark.parametrize("component", LAYOUT_PRIMITIVES)
def test_layout_primitives_allow_any_children(tmp_path: Path, component: str) -> None:
    generate_all_primitive_specs(str(tmp_path))
    spec = _load_spec(tmp_path, component)
    allowed = spec["compositionRules"]["allowedChildren"]
    assert allowed == "*", (
        f"{component}.spec.yaml compositionRules.allowedChildren expected '*', got {allowed!r}"
    )


@pytest.mark.parametrize("component", LEAF_PRIMITIVES)
def test_leaf_primitives_have_empty_allowed_children(tmp_path: Path, component: str) -> None:
    generate_all_primitive_specs(str(tmp_path))
    spec = _load_spec(tmp_path, component)
    allowed = spec["compositionRules"]["allowedChildren"]
    assert allowed == [], (
        f"{component}.spec.yaml compositionRules.allowedChildren expected [], got {allowed!r}"
    )


def test_pressable_forbids_nested_pressable(tmp_path: Path) -> None:
    generate_all_primitive_specs(str(tmp_path))
    spec = _load_spec(tmp_path, "Pressable")
    forbidden = spec["compositionRules"]["forbiddenNesting"]
    assert "Pressable" in forbidden, (
        f"Pressable.spec.yaml compositionRules.forbiddenNesting should contain 'Pressable', got {forbidden!r}"
    )


def test_pressable_is_focusable(tmp_path: Path) -> None:
    generate_all_primitive_specs(str(tmp_path))
    spec = _load_spec(tmp_path, "Pressable")
    assert spec["a11yRequirements"]["focusable"] is True, (
        "Pressable.spec.yaml a11yRequirements.focusable should be True"
    )


def test_no_hardcoded_values_in_token_bindings(tmp_path: Path) -> None:
    generate_all_primitive_specs(str(tmp_path))
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}")
    px_pattern = re.compile(r"\b\d+(?:\.\d+)?(?:px|rem|em)\b")

    for component in ALL_COMPONENTS:
        spec = _load_spec(tmp_path, component)
        for binding in spec.get("tokenBindings", []):
            value = str(binding.get("$value", ""))
            assert not hex_pattern.search(value), (
                f"{component}: hardcoded hex color in tokenBindings: {value!r}"
            )
            assert not px_pattern.search(value), (
                f"{component}: hardcoded CSS length in tokenBindings: {value!r}"
            )


def test_theme_provider_has_empty_token_bindings(tmp_path: Path) -> None:
    generate_all_primitive_specs(str(tmp_path))
    spec = _load_spec(tmp_path, "ThemeProvider")
    assert spec["tokenBindings"] == [], (
        f"ThemeProvider.spec.yaml tokenBindings should be [], got {spec['tokenBindings']!r}"
    )
