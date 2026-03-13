"""Unit tests for SpecIndexer tool (p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import pytest


def test_spec_indexer_parses_props_from_yaml(tmp_path):
    """SpecIndexer returns component metadata with props from a spec YAML."""
    from daf.tools.spec_indexer import SpecIndexer

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text(
        "name: Button\nprops:\n  - name: variant\n    type: string\n  - name: disabled\n    type: boolean\n"
    )

    indexer = SpecIndexer()
    result = indexer._run(output_dir=str(tmp_path))

    assert isinstance(result, list)
    assert len(result) == 1
    component = result[0]
    assert component["name"] == "Button"
    prop_names = [p["name"] for p in component.get("props", [])]
    assert "variant" in prop_names
    assert "disabled" in prop_names


def test_spec_indexer_returns_empty_list_when_specs_absent(tmp_path):
    """SpecIndexer returns empty list when specs/ directory does not exist."""
    from daf.tools.spec_indexer import SpecIndexer

    indexer = SpecIndexer()
    result = indexer._run(output_dir=str(tmp_path))

    assert result == []


def test_spec_indexer_handles_multiple_specs(tmp_path):
    """SpecIndexer returns one entry per spec file."""
    from daf.tools.spec_indexer import SpecIndexer

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text("name: Button\nprops: []\n")
    (specs_dir / "input.spec.yaml").write_text("name: Input\nprops: []\n")

    indexer = SpecIndexer()
    result = indexer._run(output_dir=str(tmp_path))

    assert len(result) == 2
    names = {c["name"] for c in result}
    assert "Button" in names
    assert "Input" in names


def test_spec_indexer_skips_unreadable_file(tmp_path):
    """SpecIndexer skips files that cannot be read (OSError) without raising."""
    import os
    from daf.tools.spec_indexer import SpecIndexer

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    good = specs_dir / "button.spec.yaml"
    good.write_text("name: Button\nprops: []\n")
    bad = specs_dir / "broken.spec.yaml"
    bad.write_text("name: Broken\nprops: []\n")
    # Make the file unreadable so _load_spec_file hits the OSError branch
    os.chmod(str(bad), 0o000)

    try:
        indexer = SpecIndexer()
        result = indexer._run(output_dir=str(tmp_path))
        names = {c["name"] for c in result}
        assert "Button" in names
        assert "Broken" not in names
    finally:
        os.chmod(str(bad), 0o644)


def test_spec_indexer_skips_empty_spec_file(tmp_path):
    """SpecIndexer skips spec files that parse to empty dicts."""
    from daf.tools.spec_indexer import SpecIndexer

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "empty.spec.yaml").write_text("")
    (specs_dir / "button.spec.yaml").write_text("name: Button\nprops: []\n")

    indexer = SpecIndexer()
    result = indexer._run(output_dir=str(tmp_path))

    assert len(result) == 1
    assert result[0]["name"] == "Button"
