"""Tests for PackageJsonGenerator tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

import json
from pathlib import Path


_REQUIRED_FIELDS = {"name", "version", "main", "types", "exports", "peerDependencies", "scripts"}


def test_generates_valid_package_json_with_required_fields(tmp_path: Path) -> None:
    """Generated package.json contains all required fields."""
    from daf.tools.package_json_generator import PackageJsonGenerator

    gen = PackageJsonGenerator(output_dir=str(tmp_path))
    payload = json.dumps({"name": "my-ds", "version": "v1.0.0"})
    result = gen._run(payload)
    data = json.loads(result)
    for field in _REQUIRED_FIELDS:
        assert field in data, f"Missing field: {field}"


def test_version_field_strips_v_prefix(tmp_path: Path) -> None:
    """Version in generated JSON has v-prefix stripped."""
    from daf.tools.package_json_generator import PackageJsonGenerator

    gen = PackageJsonGenerator(output_dir=str(tmp_path))
    payload = json.dumps({"name": "my-ds", "version": "v1.0.0"})
    result = gen._run(payload)
    data = json.loads(result)
    assert data["version"] == "1.0.0"


def test_experimental_version_is_handled(tmp_path: Path) -> None:
    """Experimental pre-release version is stripped of v-prefix correctly."""
    from daf.tools.package_json_generator import PackageJsonGenerator

    gen = PackageJsonGenerator(output_dir=str(tmp_path))
    payload = json.dumps({"name": "my-ds", "version": "v0.1.0-experimental"})
    result = gen._run(payload)
    data = json.loads(result)
    assert data["version"] == "0.1.0-experimental"
