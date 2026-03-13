"""Unit tests for RegistryBuilder tool (p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import json

import pytest


def test_registry_builder_writes_valid_json(tmp_path):
    """RegistryBuilder writes components.json with valid JSON."""
    from daf.tools.registry_builder import RegistryBuilder

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text(
        "name: Button\nprops:\n  - name: variant\n    type: string\n"
    )

    builder = RegistryBuilder()
    builder._run(output_dir=str(tmp_path))

    registry_file = tmp_path / "registry" / "components.json"
    assert registry_file.exists()
    data = json.loads(registry_file.read_text())
    assert isinstance(data, (list, dict))


def test_registry_builder_creates_registry_directory(tmp_path):
    """RegistryBuilder creates registry/ directory if it does not exist."""
    from daf.tools.registry_builder import RegistryBuilder

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text("name: Button\nprops: []\n")

    builder = RegistryBuilder()
    builder._run(output_dir=str(tmp_path))

    assert (tmp_path / "registry").is_dir()


def test_registry_builder_handles_spec_with_no_props(tmp_path):
    """RegistryBuilder does not raise when a spec has no props."""
    from daf.tools.registry_builder import RegistryBuilder

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "divider.spec.yaml").write_text("name: Divider\nprops: []\n")

    builder = RegistryBuilder()
    builder._run(output_dir=str(tmp_path))

    registry_file = tmp_path / "registry" / "components.json"
    assert registry_file.exists()
