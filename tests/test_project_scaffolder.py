"""Tests for ProjectScaffolder — scaffold_project_files() pure function.

All tests are unit tests using pytest's tmp_path fixture.
pipeline-config.json must be written first via generate_pipeline_config
before scaffold_project_files is callable. No LLM calls are made.
"""
from __future__ import annotations

import json
import os

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_pipeline_config(tmp_path, min_test_coverage: int = 80) -> None:
    """Write a minimal pipeline-config.json for use in scaffolder tests."""
    config = {
        "qualityGates": {"minTestCoverage": min_test_coverage},
        "lifecycle": {},
        "domains": {},
        "retry": {},
        "models": {},
        "buildConfig": {},
    }
    (tmp_path / "pipeline-config.json").write_text(json.dumps(config, indent=2))


def _make_brand_profile() -> dict:
    return {"scope": "starter", "accessibility": {"level": "AA"}}


# ---------------------------------------------------------------------------
# File presence
# ---------------------------------------------------------------------------

def test_all_three_scaffolding_files_written(tmp_path):
    from daf.tools.project_scaffolder import scaffold_project_files

    _write_pipeline_config(tmp_path)
    result = scaffold_project_files(_make_brand_profile(), str(tmp_path))
    assert (tmp_path / "tsconfig.json").exists()
    assert (tmp_path / "vitest.config.ts").exists()
    assert (tmp_path / "vite.config.ts").exists()
    assert set(result.keys()) == {"tsconfig.json", "vitest.config.ts", "vite.config.ts"}


# ---------------------------------------------------------------------------
# Content validation
# ---------------------------------------------------------------------------

def test_tsconfig_contains_required_compiler_options(tmp_path):
    from daf.tools.project_scaffolder import scaffold_project_files

    _write_pipeline_config(tmp_path)
    scaffold_project_files(_make_brand_profile(), str(tmp_path))
    tsconfig = json.loads((tmp_path / "tsconfig.json").read_text())
    opts = tsconfig["compilerOptions"]
    assert opts["target"] == "ES2020"
    assert opts["module"] == "ESNext"
    assert opts["jsx"] == "react-jsx"
    assert opts["strict"] is True
    assert opts["moduleResolution"] == "bundler"
    assert "src" in tsconfig["include"]


def test_vitest_config_reflects_coverage_threshold(tmp_path):
    from daf.tools.project_scaffolder import scaffold_project_files

    _write_pipeline_config(tmp_path, min_test_coverage=85)
    scaffold_project_files(_make_brand_profile(), str(tmp_path))
    content = (tmp_path / "vitest.config.ts").read_text()
    assert "85" in content


def test_vite_config_marks_react_as_external(tmp_path):
    from daf.tools.project_scaffolder import scaffold_project_files

    _write_pipeline_config(tmp_path)
    scaffold_project_files(_make_brand_profile(), str(tmp_path))
    content = (tmp_path / "vite.config.ts").read_text()
    assert "react" in content
    assert "es" in content
    assert "cjs" in content


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_returns_dict_with_absolute_paths(tmp_path):
    from daf.tools.project_scaffolder import scaffold_project_files

    _write_pipeline_config(tmp_path)
    result = scaffold_project_files(_make_brand_profile(), str(tmp_path))
    for path in result.values():
        assert os.path.isabs(path)
        assert os.path.exists(path)


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def test_idempotent_second_call_overwrites_without_error(tmp_path):
    from daf.tools.project_scaffolder import scaffold_project_files

    _write_pipeline_config(tmp_path)
    bp = _make_brand_profile()
    scaffold_project_files(bp, str(tmp_path))
    first = {name: (tmp_path / name).read_text() for name in ("tsconfig.json", "vitest.config.ts", "vite.config.ts")}
    scaffold_project_files(bp, str(tmp_path))
    second = {name: (tmp_path / name).read_text() for name in ("tsconfig.json", "vitest.config.ts", "vite.config.ts")}
    assert first == second


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_missing_pipeline_config_raises_error(tmp_path):
    from daf.tools.project_scaffolder import scaffold_project_files

    with pytest.raises((FileNotFoundError, ValueError)):
        scaffold_project_files(_make_brand_profile(), str(tmp_path))


def test_tsconfig_is_valid_json(tmp_path):
    from daf.tools.project_scaffolder import scaffold_project_files

    _write_pipeline_config(tmp_path)
    scaffold_project_files(_make_brand_profile(), str(tmp_path))
    text = (tmp_path / "tsconfig.json").read_text()
    parsed = json.loads(text)
    assert isinstance(parsed, dict)
