"""Tests for ConfigGenerator — generate_pipeline_config() pure function.

All tests are unit tests using pytest's tmp_path fixture.
No LLM calls are made. Tests cover schema completeness, field derivation,
model env var resolution, and error cases.
"""
from __future__ import annotations

import json
import os

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_brand_profile(scope: str = "starter", a11y_level: str = "AA") -> dict:
    return {
        "scope": scope,
        "accessibility": {"level": a11y_level},
    }


# ---------------------------------------------------------------------------
# Schema completeness
# ---------------------------------------------------------------------------

def test_generated_config_has_all_top_level_keys(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    out = generate_pipeline_config(_make_brand_profile(), str(tmp_path))
    config = json.loads((tmp_path / "pipeline-config.json").read_text())
    for key in ("qualityGates", "lifecycle", "domains", "retry", "models", "buildConfig"):
        assert key in config, f"Missing top-level key: {key}"


# ---------------------------------------------------------------------------
# Accessibility × scope derivation
# ---------------------------------------------------------------------------

def test_aa_accessibility_standard_scope_thresholds(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    generate_pipeline_config(_make_brand_profile("standard", "AA"), str(tmp_path))
    config = json.loads((tmp_path / "pipeline-config.json").read_text())
    assert config["qualityGates"]["minCompositeScore"] == 70
    assert config["qualityGates"]["minTestCoverage"] == 80
    assert config["qualityGates"]["a11yLevel"] == "AA"


def test_aaa_accessibility_raises_composite_score_to_85(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    generate_pipeline_config(_make_brand_profile("starter", "AAA"), str(tmp_path))
    config = json.loads((tmp_path / "pipeline-config.json").read_text())
    assert config["qualityGates"]["minCompositeScore"] == 85
    assert config["qualityGates"]["a11yLevel"] == "AAA"


# ---------------------------------------------------------------------------
# Scope tier derivation
# ---------------------------------------------------------------------------

def test_comprehensive_scope_produces_beta_components_and_domains(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    generate_pipeline_config(_make_brand_profile("comprehensive", "AA"), str(tmp_path))
    config = json.loads((tmp_path / "pipeline-config.json").read_text())
    beta = config["lifecycle"]["betaComponents"]
    assert beta == ["DatePicker", "DataGrid", "TreeView", "Drawer", "Stepper", "FileUpload", "RichText"]
    cats = config["domains"]["categories"]
    assert "data-entry" in cats
    assert "navigation" in cats
    assert "data-display" in cats
    assert config["qualityGates"]["minTestCoverage"] == 75


def test_starter_scope_empty_beta_and_minimal_domains(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    generate_pipeline_config(_make_brand_profile("starter"), str(tmp_path))
    config = json.loads((tmp_path / "pipeline-config.json").read_text())
    assert config["lifecycle"]["betaComponents"] == []
    cats = config["domains"]["categories"]
    assert "navigation" not in cats
    assert "data-entry" not in cats
    for required in ("forms", "layout", "feedback"):
        assert required in cats


def test_standard_scope_has_navigation_not_data_entry(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    generate_pipeline_config(_make_brand_profile("standard"), str(tmp_path))
    config = json.loads((tmp_path / "pipeline-config.json").read_text())
    cats = config["domains"]["categories"]
    assert "navigation" in cats
    assert "data-display" in cats
    assert "data-entry" not in cats


# ---------------------------------------------------------------------------
# Fixed default fields
# ---------------------------------------------------------------------------

def test_fixed_default_fields(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    generate_pipeline_config(_make_brand_profile(), str(tmp_path))
    config = json.loads((tmp_path / "pipeline-config.json").read_text())
    assert config["qualityGates"]["blockOnWarnings"] is False
    assert config["lifecycle"]["defaultStatus"] == "stable"
    assert config["lifecycle"]["deprecationGracePeriodDays"] == 90
    assert config["domains"]["autoAssign"] is True
    assert config["retry"]["maxComponentRetries"] == 3
    assert config["retry"]["maxCrewRetries"] == 2
    assert config["buildConfig"]["tsTarget"] == "ES2020"
    assert config["buildConfig"]["moduleFormat"] == "ESNext"
    assert config["buildConfig"]["cssModules"] is False


# ---------------------------------------------------------------------------
# Model env var resolution
# ---------------------------------------------------------------------------

def test_model_identifiers_from_env_vars(tmp_path, monkeypatch):
    from daf.tools.config_generator import generate_pipeline_config

    monkeypatch.setenv("DAF_TIER1_MODEL", "claude-opus-4-custom")
    monkeypatch.delenv("DAF_TIER2_MODEL", raising=False)
    monkeypatch.delenv("DAF_TIER3_MODEL", raising=False)
    generate_pipeline_config(_make_brand_profile(), str(tmp_path))
    config = json.loads((tmp_path / "pipeline-config.json").read_text())
    assert config["models"]["tier1"] == "claude-opus-4-custom"
    assert config["models"]["tier2"] == "claude-sonnet-4-20250514"
    assert config["models"]["tier3"] == "claude-haiku-4-20250414"


def test_model_defaults_when_no_env_vars_set(tmp_path, monkeypatch):
    from daf.tools.config_generator import generate_pipeline_config

    monkeypatch.delenv("DAF_TIER1_MODEL", raising=False)
    monkeypatch.delenv("DAF_TIER2_MODEL", raising=False)
    monkeypatch.delenv("DAF_TIER3_MODEL", raising=False)
    generate_pipeline_config(_make_brand_profile(), str(tmp_path))
    config = json.loads((tmp_path / "pipeline-config.json").read_text())
    assert config["models"]["tier1"] == "claude-opus-4-20250514"
    assert config["models"]["tier2"] == "claude-sonnet-4-20250514"
    assert config["models"]["tier3"] == "claude-haiku-4-20250414"


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def test_output_is_valid_json(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    generate_pipeline_config(_make_brand_profile(), str(tmp_path))
    text = (tmp_path / "pipeline-config.json").read_text()
    parsed = json.loads(text)
    assert isinstance(parsed, dict)


def test_returns_absolute_path_to_written_file(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    result = generate_pipeline_config(_make_brand_profile(), str(tmp_path))
    assert isinstance(result, str)
    assert os.path.isabs(result)
    assert os.path.exists(result)


def test_idempotent_second_call_overwrites_without_error(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    bp = _make_brand_profile("standard", "AA")
    generate_pipeline_config(bp, str(tmp_path))
    first = (tmp_path / "pipeline-config.json").read_text()
    generate_pipeline_config(bp, str(tmp_path))
    second = (tmp_path / "pipeline-config.json").read_text()
    assert first == second


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_missing_accessibility_key_raises_error(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    with pytest.raises((KeyError, ValueError)):
        generate_pipeline_config({"scope": "starter"}, str(tmp_path))


def test_missing_scope_key_raises_error(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    with pytest.raises((KeyError, ValueError)):
        generate_pipeline_config({"accessibility": {"level": "AA"}}, str(tmp_path))


# ---------------------------------------------------------------------------
# Specific count assertions
# ---------------------------------------------------------------------------

def test_comprehensive_beta_list_has_exactly_7_names(tmp_path):
    from daf.tools.config_generator import generate_pipeline_config

    generate_pipeline_config(_make_brand_profile("comprehensive"), str(tmp_path))
    config = json.loads((tmp_path / "pipeline-config.json").read_text())
    assert len(config["lifecycle"]["betaComponents"]) == 7
