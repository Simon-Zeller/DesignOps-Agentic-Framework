"""Tests for generate_component_specs and CoreComponentSpecGenerator (p07).

TDD approach: these tests define the contract before implementation.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from daf.tools.core_component_spec_generator import (
    CoreComponentSpecGenerator,
    generate_component_specs,
)

# ---------------------------------------------------------------------------
# Constants used across multiple tests
# ---------------------------------------------------------------------------

_STARTER_NAMES = [
    "Button", "Input", "Checkbox", "Radio", "Select",
    "Card", "Badge", "Avatar", "Alert", "Modal",
]

_STANDARD_DELTA_NAMES = [
    "Table", "Tabs", "Accordion", "Tooltip", "Toast",
    "Dropdown", "Pagination", "Breadcrumb", "Navigation",
]

_COMPREHENSIVE_DELTA_NAMES = [
    "DatePicker", "DataGrid", "TreeView", "Drawer",
    "Stepper", "FileUpload", "RichText",
]

_ALL_COMPREHENSIVE_NAMES = (
    _STARTER_NAMES + _STANDARD_DELTA_NAMES + _COMPREHENSIVE_DELTA_NAMES
)

_PRIMITIVE_NAMES = {
    "Box", "Stack", "HStack", "VStack", "Grid",
    "Text", "Icon", "Pressable", "Divider", "Spacer", "ThemeProvider",
}

_REQUIRED_FIELDS = [
    "component", "description", "props", "variants",
    "states", "tokenBindings", "compositionRules", "a11yRequirements",
]

_REQUIRED_A11Y_FIELDS = ["role", "focusable", "keyboardInteractions", "ariaAttributes"]


# ---------------------------------------------------------------------------
# Scope file count tests
# ---------------------------------------------------------------------------


def test_starter_scope_produces_10_files(tmp_path: Path) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    specs = list((tmp_path / "specs").glob("*.spec.yaml"))
    assert len(specs) == 10


def test_standard_scope_produces_19_files(tmp_path: Path) -> None:
    generate_component_specs(scope="standard", output_dir=str(tmp_path))
    specs = list((tmp_path / "specs").glob("*.spec.yaml"))
    assert len(specs) == 19


def test_comprehensive_scope_produces_26_files(tmp_path: Path) -> None:
    generate_component_specs(scope="comprehensive", output_dir=str(tmp_path))
    specs = list((tmp_path / "specs").glob("*.spec.yaml"))
    assert len(specs) == 26


# ---------------------------------------------------------------------------
# Return value tests
# ---------------------------------------------------------------------------


def test_function_returns_dict_with_absolute_paths(tmp_path: Path) -> None:
    result = generate_component_specs(scope="starter", output_dir=str(tmp_path))
    assert isinstance(result, dict)
    assert len(result) == 10
    for name, path_str in result.items():
        assert isinstance(path_str, str)
        p = Path(path_str)
        assert p.is_absolute()
        assert p.exists()


# ---------------------------------------------------------------------------
# Idempotency & directory creation
# ---------------------------------------------------------------------------


def test_generate_is_idempotent(tmp_path: Path) -> None:
    result1 = generate_component_specs(scope="starter", output_dir=str(tmp_path))
    result2 = generate_component_specs(scope="starter", output_dir=str(tmp_path))
    assert result1 == result2
    # File content must be unchanged
    for path_str in result1.values():
        p = Path(path_str)
        content1 = p.read_text(encoding="utf-8")
        result2_path = Path(result2[list(result1.keys())[list(result1.values()).index(path_str)]])
        content2 = result2_path.read_text(encoding="utf-8")
        assert content1 == content2


def test_specs_dir_created_automatically(tmp_path: Path) -> None:
    assert not (tmp_path / "specs").exists()
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    assert (tmp_path / "specs").is_dir()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_invalid_scope_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError) as exc_info:
        generate_component_specs(scope="enterprise", output_dir=str(tmp_path))
    msg = str(exc_info.value).lower()
    assert "starter" in msg
    assert "standard" in msg
    assert "comprehensive" in msg


# ---------------------------------------------------------------------------
# Required fields per spec
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", _STARTER_NAMES)
def test_each_starter_spec_has_required_fields(tmp_path: Path, name: str) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec_path = tmp_path / "specs" / f"{name}.spec.yaml"
    assert spec_path.exists(), f"Missing spec file: {spec_path}"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    for field in _REQUIRED_FIELDS:
        assert field in spec, f"{name}: missing field '{field}'"


@pytest.mark.parametrize("name", _ALL_COMPREHENSIVE_NAMES)
def test_component_field_matches_filename_stem(tmp_path: Path, name: str) -> None:
    generate_component_specs(scope="comprehensive", output_dir=str(tmp_path))
    spec_path = tmp_path / "specs" / f"{name}.spec.yaml"
    assert spec_path.exists(), f"Missing spec file: {spec_path}"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    assert spec["component"] == name


# ---------------------------------------------------------------------------
# Props structure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", _STARTER_NAMES)
def test_each_prop_has_type_required_default(tmp_path: Path, name: str) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec_path = tmp_path / "specs" / f"{name}.spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    props = spec.get("props", {})
    assert props, f"{name}: props must not be empty"
    for prop_name, prop_def in props.items():
        assert "type" in prop_def, f"{name}.props.{prop_name}: missing 'type'"
        assert "required" in prop_def, f"{name}.props.{prop_name}: missing 'required'"
        assert "default" in prop_def, f"{name}.props.{prop_name}: missing 'default'"


# ---------------------------------------------------------------------------
# Token binding checks — no hardcoded values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", _ALL_COMPREHENSIVE_NAMES)
def test_no_hardcoded_hex_in_token_bindings(tmp_path: Path, name: str) -> None:
    generate_component_specs(scope="comprehensive", output_dir=str(tmp_path))
    spec_path = tmp_path / "specs" / f"{name}.spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    for entry in spec.get("tokenBindings", []):
        value = entry.get("$value", "")
        assert not re.search(r"#[0-9a-fA-F]{3,8}", str(value)), (
            f"{name}: hardcoded hex found in tokenBindings: {value}"
        )


@pytest.mark.parametrize("name", _ALL_COMPREHENSIVE_NAMES)
def test_no_hardcoded_length_in_token_bindings(tmp_path: Path, name: str) -> None:
    generate_component_specs(scope="comprehensive", output_dir=str(tmp_path))
    spec_path = tmp_path / "specs" / f"{name}.spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    for entry in spec.get("tokenBindings", []):
        value = str(entry.get("$value", ""))
        assert not re.search(r"\d+(?:px|rem|em)\b", value), (
            f"{name}: hardcoded length literal found in tokenBindings: {value}"
        )


def test_input_spec_has_semantic_color_token(tmp_path: Path) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / "Input.spec.yaml").read_text(encoding="utf-8"))
    token_values = [entry.get("$value", "") for entry in spec.get("tokenBindings", [])]
    assert any(
        "color.border" in v or "color.interactive" in v for v in token_values
    ), f"Input.spec.yaml must reference color.border or color.interactive token; got: {token_values}"


# ---------------------------------------------------------------------------
# Composition rules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", _STARTER_NAMES)
def test_all_starter_components_have_nonempty_composes_from(tmp_path: Path, name: str) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / f"{name}.spec.yaml").read_text(encoding="utf-8"))
    composes_from = spec["compositionRules"]["composesFrom"]
    assert composes_from, f"{name}: composesFrom must not be empty"
    for p in composes_from:
        assert p in _PRIMITIVE_NAMES, (
            f"{name}: composesFrom contains non-primitive '{p}'"
        )


@pytest.mark.parametrize("name", _ALL_COMPREHENSIVE_NAMES)
def test_no_component_references_component_in_composes_from(tmp_path: Path, name: str) -> None:
    generate_component_specs(scope="comprehensive", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / f"{name}.spec.yaml").read_text(encoding="utf-8"))
    composes_from = spec["compositionRules"].get("composesFrom", [])
    component_names_set = set(_ALL_COMPREHENSIVE_NAMES)
    for entry in composes_from:
        assert entry not in component_names_set, (
            f"{name}.composesFrom: contains component name '{entry}' (must be primitives only)"
        )


def test_button_composes_from_pressable(tmp_path: Path) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / "Button.spec.yaml").read_text(encoding="utf-8"))
    assert "Pressable" in spec["compositionRules"]["composesFrom"]


def test_card_composes_from_box(tmp_path: Path) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / "Card.spec.yaml").read_text(encoding="utf-8"))
    assert "Box" in spec["compositionRules"]["composesFrom"]


def test_modal_has_slot_definitions(tmp_path: Path) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / "Modal.spec.yaml").read_text(encoding="utf-8"))
    slots = spec["compositionRules"].get("slots", [])
    assert slots, "Modal.spec.yaml: compositionRules.slots must be non-empty"


@pytest.mark.parametrize("name", _STARTER_NAMES)
def test_all_specs_have_forbidden_nesting_field(tmp_path: Path, name: str) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / f"{name}.spec.yaml").read_text(encoding="utf-8"))
    assert "forbiddenNesting" in spec["compositionRules"], (
        f"{name}: compositionRules must have 'forbiddenNesting' key"
    )


# ---------------------------------------------------------------------------
# States
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["Button", "Input", "Checkbox", "Radio", "Select"])
def test_interactive_starter_components_have_hover_focus_disabled_states(
    tmp_path: Path, name: str
) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / f"{name}.spec.yaml").read_text(encoding="utf-8"))
    states = spec.get("states", {})
    for required in ("default", "hover", "focus", "disabled"):
        assert required in states, f"{name}: states must include '{required}'"


@pytest.mark.parametrize("name", ["Input", "Checkbox", "Radio", "Select"])
def test_form_components_have_error_and_success_states(tmp_path: Path, name: str) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / f"{name}.spec.yaml").read_text(encoding="utf-8"))
    states = spec.get("states", {})
    assert "error" in states, f"{name}: states must include 'error'"
    assert "success" in states, f"{name}: states must include 'success'"


def test_badge_has_default_state(tmp_path: Path) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / "Badge.spec.yaml").read_text(encoding="utf-8"))
    assert "default" in spec.get("states", {}), "Badge.spec.yaml: states must have 'default'"


# ---------------------------------------------------------------------------
# Accessibility requirements
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", _STARTER_NAMES)
def test_all_starter_components_have_a11y_required_fields(tmp_path: Path, name: str) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / f"{name}.spec.yaml").read_text(encoding="utf-8"))
    a11y = spec.get("a11yRequirements", {})
    for field in _REQUIRED_A11Y_FIELDS:
        assert field in a11y, f"{name}: a11yRequirements must have '{field}'"


def test_button_keyboard_interactions_include_enter_and_space(tmp_path: Path) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / "Button.spec.yaml").read_text(encoding="utf-8"))
    ki = spec["a11yRequirements"]["keyboardInteractions"]
    ki_str = str(ki)
    assert "Enter" in ki_str, "Button: keyboardInteractions must reference Enter"
    assert "Space" in ki_str, "Button: keyboardInteractions must reference Space"


def test_modal_a11y(tmp_path: Path) -> None:
    generate_component_specs(scope="starter", output_dir=str(tmp_path))
    spec = yaml.safe_load((tmp_path / "specs" / "Modal.spec.yaml").read_text(encoding="utf-8"))
    a11y = spec["a11yRequirements"]
    assert a11y["role"] == "dialog"
    assert a11y["focusable"] is True
    ki_str = str(a11y["keyboardInteractions"])
    assert "Escape" in ki_str
    aria_str = str(a11y["ariaAttributes"])
    assert "aria-modal" in aria_str or "aria-labelledby" in aria_str


# ---------------------------------------------------------------------------
# Override tests
# ---------------------------------------------------------------------------


def test_override_patches_target_component(tmp_path: Path) -> None:
    generate_component_specs(
        scope="starter",
        output_dir=str(tmp_path),
        component_overrides={"Button": {"defaultVariant": "secondary"}},
    )
    button_spec = yaml.safe_load(
        (tmp_path / "specs" / "Button.spec.yaml").read_text(encoding="utf-8")
    )
    assert button_spec.get("defaultVariant") == "secondary"
    # Input must be unaffected
    input_spec = yaml.safe_load(
        (tmp_path / "specs" / "Input.spec.yaml").read_text(encoding="utf-8")
    )
    assert "defaultVariant" not in input_spec


def test_override_for_out_of_scope_component_ignored(tmp_path: Path) -> None:
    result = generate_component_specs(
        scope="starter",
        output_dir=str(tmp_path),
        component_overrides={"DataGrid": {"pageSize": 50}},
    )
    specs = list((tmp_path / "specs").glob("*.spec.yaml"))
    assert len(specs) == 10
    assert len(result) == 10


def test_none_overrides_same_as_empty_dict(tmp_path: Path) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as dir_a, tempfile.TemporaryDirectory() as dir_b:
        generate_component_specs(scope="starter", output_dir=dir_a, component_overrides=None)
        generate_component_specs(scope="starter", output_dir=dir_b, component_overrides={})
        for name in _STARTER_NAMES:
            content_a = (Path(dir_a) / "specs" / f"{name}.spec.yaml").read_text(encoding="utf-8")
            content_b = (Path(dir_b) / "specs" / f"{name}.spec.yaml").read_text(encoding="utf-8")
            assert content_a == content_b, f"{name}: content differs between None and {{}} overrides"


def test_comprehensive_scope_does_not_include_primitive_names(tmp_path: Path) -> None:
    generate_component_specs(scope="comprehensive", output_dir=str(tmp_path))
    specs_dir = tmp_path / "specs"
    for prim in ["Box", "Stack", "HStack", "VStack", "Grid", "Text", "Icon",
                 "Pressable", "Divider", "Spacer"]:
        assert not (specs_dir / f"{prim}.spec.yaml").exists(), (
            f"Primitive '{prim}' must not appear in component specs output"
        )
