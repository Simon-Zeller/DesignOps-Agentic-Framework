"""Tests for ComponentInventoryReader tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path


def test_returns_component_list_from_specs(tmp_path: Path) -> None:
    """Returns component entries for each spec YAML in specs/."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text("name: Button\nstatus: stable\n")
    (specs_dir / "input.spec.yaml").write_text("name: Input\nstatus: beta\n")

    from daf.tools.component_inventory_reader import ComponentInventoryReader

    reader = ComponentInventoryReader(output_dir=str(tmp_path))
    result = reader._run("")
    assert "components" in result
    names = [c["name"] for c in result["components"]]
    assert "Button" in names
    assert "Input" in names


def test_returns_empty_list_when_specs_absent(tmp_path: Path) -> None:
    """Returns {'components': []} when specs/ directory does not exist."""
    from daf.tools.component_inventory_reader import ComponentInventoryReader

    reader = ComponentInventoryReader(output_dir=str(tmp_path))
    result = reader._run("")
    assert result == {"components": []}


def test_handles_malformed_yaml_gracefully(tmp_path: Path) -> None:
    """Skips malformed YAML files without raising an exception."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "broken.spec.yaml").write_text(": invalid: yaml: [\n")
    (specs_dir / "valid.spec.yaml").write_text("name: Valid\nstatus: stable\n")

    from daf.tools.component_inventory_reader import ComponentInventoryReader

    reader = ComponentInventoryReader(output_dir=str(tmp_path))
    result = reader._run("")
    assert "components" in result
    names = [c["name"] for c in result["components"]]
    assert "Valid" in names
