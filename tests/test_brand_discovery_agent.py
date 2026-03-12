"""Tests for the Brand Discovery Agent (Agent 1) and its four tools.

Follows strict TDD order: tests written before implementation.
Run with: pytest tests/test_brand_discovery_agent.py -v -m "not integration"
"""
from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner
from unittest.mock import patch

from daf.cli import app, render_gate_summary
from daf.models import BrandProfile, ColorsConfig
from daf.tools.brand_profile_validator import BrandProfileSchemaValidator
from daf.tools.archetype_resolver import ArchetypeResolver
from daf.tools.consistency_checker import ConsistencyChecker
from daf.tools.default_filler import DefaultFiller


runner = CliRunner()

# All optional §6 top-level keys that ArchetypeResolver must cover
_REQUIRED_DEFAULT_KEYS = {
    "colors",
    "typography",
    "spacing",
    "borderRadius",
    "elevation",
    "motion",
    "themes",
    "accessibility",
    "componentScope",
    "breakpoints",
}


# ─────────────────────────────────────────────────────────────
# BrandProfileSchemaValidator
# ─────────────────────────────────────────────────────────────


class TestBrandProfileSchemaValidator:
    def test_valid_minimal_profile_passes(self) -> None:
        profile = {"name": "Acme", "archetype": "enterprise-b2b"}
        result = BrandProfileSchemaValidator()._run(profile)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_missing_name_returns_structured_error(self) -> None:
        profile = {"archetype": "consumer-b2c"}
        result = BrandProfileSchemaValidator()._run(profile)
        assert result["valid"] is False
        fields = [e["field"] for e in result["errors"]]
        assert "name" in fields

    @pytest.mark.parametrize("archetype", ["b2b", "ENTERPRISE", "", "unknown"])
    def test_invalid_archetype_rejected(self, archetype: str) -> None:
        profile = {"name": "X", "archetype": archetype}
        result = BrandProfileSchemaValidator()._run(profile)
        assert result["valid"] is False
        fields = [e["field"] for e in result["errors"]]
        assert "archetype" in fields

    @pytest.mark.parametrize(
        "hex_val", ["zz9900", "rgb(0,0,255)", "red", "#12345", "#GGGGGG"]
    )
    def test_invalid_hex_color_rejected(self, hex_val: str) -> None:
        profile = {
            "name": "X",
            "archetype": "enterprise-b2b",
            "colors": {"primary": hex_val},
        }
        result = BrandProfileSchemaValidator()._run(profile)
        assert result["valid"] is False
        fields = [e["field"] for e in result["errors"]]
        assert "colors.primary" in fields
        color_errors = [e for e in result["errors"] if e["field"] == "colors.primary"]
        assert any("hex" in e["message"].lower() or "#" in e["message"] for e in color_errors)

    def test_natural_language_color_passes(self) -> None:
        profile = {
            "name": "X",
            "archetype": "enterprise-b2b",
            "colors": {"primary": "a warm corporate red"},
        }
        result = BrandProfileSchemaValidator()._run(profile)
        assert result["valid"] is True
        assert result["errors"] == []

    @pytest.mark.parametrize("ratio", [0.9, 0.0, 2.1, 3.5, -1.0])
    def test_scale_ratio_out_of_bounds_rejected(self, ratio: float) -> None:
        profile = {
            "name": "X",
            "archetype": "enterprise-b2b",
            "typography": {"scaleRatio": ratio},
        }
        result = BrandProfileSchemaValidator()._run(profile)
        assert result["valid"] is False
        fields = [e["field"] for e in result["errors"]]
        assert "typography.scaleRatio" in fields

    def test_empty_profile_has_both_required_field_errors(self) -> None:
        result = BrandProfileSchemaValidator()._run({})
        assert result["valid"] is False
        fields = [e["field"] for e in result["errors"]]
        assert "name" in fields
        assert "archetype" in fields

    def test_unknown_archetype_rejected(self) -> None:
        profile = {"name": "X", "archetype": "startup"}
        result = BrandProfileSchemaValidator()._run(profile)
        assert result["valid"] is False
        fields = [e["field"] for e in result["errors"]]
        assert "archetype" in fields


# ─────────────────────────────────────────────────────────────
# ArchetypeResolver
# ─────────────────────────────────────────────────────────────


class TestArchetypeResolver:
    @pytest.mark.parametrize(
        "archetype",
        ["enterprise-b2b", "consumer-b2c", "mobile-first", "multi-brand", "custom"],
    )
    def test_all_archetypes_return_complete_defaults(self, archetype: str) -> None:
        result = ArchetypeResolver()._run(archetype)
        for key in _REQUIRED_DEFAULT_KEYS:
            assert key in result, f"Missing '{key}' for archetype '{archetype}'"
            assert result[key] is not None, f"'{key}' is None for archetype '{archetype}'"

    def test_enterprise_b2b_defaults_match_spec(self) -> None:
        result = ArchetypeResolver()._run("enterprise-b2b")
        assert result["accessibility"] == "AA"
        assert result["componentScope"] == "comprehensive"
        assert result["spacing"]["density"] == "compact"
        assert result["borderRadius"] == "subtle"

    def test_mobile_first_defaults_match_spec(self) -> None:
        result = ArchetypeResolver()._run("mobile-first")
        assert result["accessibility"] == "AAA"
        assert result["componentScope"] == "starter"
        assert result["spacing"]["density"] == "compact"
        assert result["breakpoints"]["strategy"] == "mobile-first"

    def test_multi_brand_enables_overrides_and_all_themes(self) -> None:
        result = ArchetypeResolver()._run("multi-brand")
        assert result["themes"]["brandOverrides"] is True
        modes = result["themes"]["modes"]
        assert "light" in modes
        assert "dark" in modes
        assert "high-contrast" in modes

    def test_custom_archetype_uses_universal_baseline(self) -> None:
        resolver_result = ArchetypeResolver()._run("custom")
        filler_result = DefaultFiller()._run(
            {"name": "X", "archetype": "custom"}, resolver_result
        )
        for key in _REQUIRED_DEFAULT_KEYS:
            assert key in filler_result, f"Missing '{key}' after custom default fill"
            assert filler_result[key] is not None


# ─────────────────────────────────────────────────────────────
# ConsistencyChecker
# ─────────────────────────────────────────────────────────────


class TestConsistencyChecker:
    def test_consistent_enterprise_profile_returns_empty(self) -> None:
        profile = {
            "archetype": "enterprise-b2b",
            "spacing": {"density": "compact", "baseUnit": 4},
            "componentScope": "comprehensive",
            "accessibility": "AA",
        }
        result = ConsistencyChecker()._run(profile)
        assert result == []

    def test_compact_density_large_base_unit_is_error(self) -> None:
        profile = {
            "archetype": "enterprise-b2b",
            "spacing": {"density": "compact", "baseUnit": 16},
        }
        result = ConsistencyChecker()._run(profile)
        error_findings = [f for f in result if f["severity"] == "error"]
        assert len(error_findings) >= 1
        fields = [f["field"] for f in error_findings]
        assert "spacing" in fields

    def test_mobile_first_comprehensive_scope_is_warning_not_error(self) -> None:
        profile = {"archetype": "mobile-first", "componentScope": "comprehensive"}
        result = ConsistencyChecker()._run(profile)
        assert len(result) >= 1
        assert all(f["severity"] == "warning" for f in result)
        fields = [f["field"] for f in result]
        assert "componentScope" in fields

    def test_multi_brand_brand_overrides_false_is_warning(self) -> None:
        profile = {
            "archetype": "multi-brand",
            "themes": {"brandOverrides": False},
        }
        result = ConsistencyChecker()._run(profile)
        severities = {f["severity"] for f in result}
        assert "error" not in severities
        assert "warning" in severities
        fields = [f["field"] for f in result]
        assert "themes.brandOverrides" in fields

    def test_expressive_motion_with_aaa_is_warning(self) -> None:
        profile = {"motion": "expressive", "accessibility": "AAA"}
        result = ConsistencyChecker()._run(profile)
        severities = {f["severity"] for f in result}
        assert "error" not in severities
        assert "warning" in severities
        fields = [f["field"] for f in result]
        assert "motion" in fields

    def test_consistent_multi_brand_returns_empty(self) -> None:
        profile = {
            "archetype": "multi-brand",
            "themes": {
                "brandOverrides": True,
                "modes": ["light", "dark", "high-contrast"],
            },
            "accessibility": "AA",
            "componentScope": "standard",
        }
        result = ConsistencyChecker()._run(profile)
        assert result == []


# ─────────────────────────────────────────────────────────────
# DefaultFiller
# ─────────────────────────────────────────────────────────────


class TestDefaultFiller:
    def _enterprise_defaults(self) -> dict:
        return ArchetypeResolver()._run("enterprise-b2b")

    def _consumer_defaults(self) -> dict:
        return ArchetypeResolver()._run("consumer-b2c")

    def test_user_specified_values_are_not_overridden(self) -> None:
        profile = {
            "name": "Acme",
            "archetype": "enterprise-b2b",
            "colors": {"primary": "#1a73e8"},
            "accessibility": "AAA",
        }
        defaults = self._enterprise_defaults()
        result = DefaultFiller()._run(profile, defaults)
        assert result["colors"]["primary"] == "#1a73e8"
        assert result["accessibility"] == "AAA"

    def test_minimal_profile_gains_all_optional_fields(self) -> None:
        profile = {"name": "Acme", "archetype": "consumer-b2c"}
        defaults = self._consumer_defaults()
        result = DefaultFiller()._run(profile, defaults)
        for key in _REQUIRED_DEFAULT_KEYS:
            assert key in result, f"Missing '{key}' after fill"
            assert result[key] is not None
        assert isinstance(result["_filled_fields"], list)
        assert len(result["_filled_fields"]) > 0

    def test_filled_fields_tracks_defaulted_not_user_specified(self) -> None:
        profile = {"name": "Acme", "archetype": "enterprise-b2b"}
        defaults = self._enterprise_defaults()
        result = DefaultFiller()._run(profile, defaults)
        filled = result["_filled_fields"]
        # At least spacing and componentScope should be tracked as filled
        assert any("spacing" in f for f in filled)
        assert "componentScope" in filled
        # Required fields set by the user are never in _filled_fields
        assert "name" not in filled
        assert "archetype" not in filled


# ─────────────────────────────────────────────────────────────
# BrandProfile Pydantic model
# ─────────────────────────────────────────────────────────────


class TestBrandProfileModel:
    def test_valid_complete_profile_constructs(self) -> None:
        data = {
            "name": "Acme",
            "archetype": "enterprise-b2b",
            "colors": {"primary": "#003366"},
            "accessibility": "AA",
            "componentScope": "comprehensive",
        }
        profile = BrandProfile(**data)
        assert profile.name == "Acme"
        assert profile.archetype == "enterprise-b2b"
        assert profile.accessibility == "AA"

    def test_extra_fields_are_stripped(self) -> None:
        data = {
            "name": "X",
            "archetype": "enterprise-b2b",
            "_internal_note": "strip me",
            "hallucinated_field": 42,
        }
        profile = BrandProfile(**data)
        assert not hasattr(profile, "_internal_note")
        assert not hasattr(profile, "hallucinated_field")


# ─────────────────────────────────────────────────────────────
# daf generate CLI command
# ─────────────────────────────────────────────────────────────


def _mock_profile() -> BrandProfile:
    return BrandProfile(
        name="Acme",
        archetype="enterprise-b2b",
        accessibility="AA",
        componentScope="comprehensive",
        filled_fields=["spacing.density", "componentScope"],
    )


class TestGenerateCLI:
    def test_missing_profile_exits_code_1(
        self, tmp_path: object, monkeypatch: object
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["generate"])
        assert result.exit_code == 1
        assert "No brand-profile.json found" in result.output

    def test_profile_flag_loads_from_path(self, tmp_path: object) -> None:
        profile_path = tmp_path / "my-profile.json"  # type: ignore[operator]
        profile_path.write_text(
            json.dumps({"name": "Test", "archetype": "enterprise-b2b"})
        )
        with patch("daf.cli.run_brand_discovery", return_value=_mock_profile()):
            result = runner.invoke(
                app, ["generate", "--profile", str(profile_path), "--yes"]
            )
        assert result.exit_code == 0

    def test_yes_flag_skips_gate(
        self, tmp_path: object, monkeypatch: object
    ) -> None:
        monkeypatch.chdir(tmp_path)
        profile_path = tmp_path / "brand-profile.json"  # type: ignore[operator]
        profile_path.write_text(
            json.dumps({"name": "Test", "archetype": "enterprise-b2b"})
        )
        with patch("daf.cli.run_brand_discovery", return_value=_mock_profile()):
            result = runner.invoke(app, ["generate", "--yes"])
        assert result.exit_code == 0
        assert "Approve this brand profile" not in result.output

    def test_gate_approval_writes_profile(
        self, tmp_path: object, monkeypatch: object
    ) -> None:
        monkeypatch.chdir(tmp_path)
        profile_path = tmp_path / "brand-profile.json"  # type: ignore[operator]
        profile_path.write_text(
            json.dumps({"name": "Test", "archetype": "enterprise-b2b"})
        )
        with patch("daf.cli.run_brand_discovery", return_value=_mock_profile()):
            result = runner.invoke(app, ["generate"], input="y\n")
        assert result.exit_code == 0
        written = json.loads(profile_path.read_text())  # type: ignore[attr-defined]
        assert written["name"] == "Acme"

    def test_gate_rejection_does_not_write_profile(
        self, tmp_path: object, monkeypatch: object
    ) -> None:
        monkeypatch.chdir(tmp_path)
        profile_path = tmp_path / "brand-profile.json"  # type: ignore[operator]
        original_content = json.dumps({"name": "Test", "archetype": "enterprise-b2b"})
        profile_path.write_text(original_content)
        with patch("daf.cli.run_brand_discovery", return_value=_mock_profile()):
            result = runner.invoke(app, ["generate"], input="N\n")
        assert result.exit_code == 1
        # File should remain as original (not overwritten)
        assert profile_path.read_text() == original_content  # type: ignore[attr-defined]

    def test_enter_at_gate_is_rejection(
        self, tmp_path: object, monkeypatch: object
    ) -> None:
        monkeypatch.chdir(tmp_path)
        profile_path = tmp_path / "brand-profile.json"  # type: ignore[operator]
        profile_path.write_text(
            json.dumps({"name": "Test", "archetype": "enterprise-b2b"})
        )
        with patch("daf.cli.run_brand_discovery", return_value=_mock_profile()):
            result = runner.invoke(app, ["generate"], input="\n")
        assert result.exit_code == 1


# ─────────────────────────────────────────────────────────────
# Human Gate summary display
# ─────────────────────────────────────────────────────────────


class TestGateSummaryDisplay:
    def test_default_vs_specified_labels(self) -> None:
        profile = BrandProfile(
            name="Acme",
            archetype="enterprise-b2b",
            componentScope="comprehensive",
            colors=ColorsConfig(primary="#003366"),
            filled_fields=["componentScope"],
        )
        summary = render_gate_summary(profile)
        # The line containing componentScope should have (default) label
        lines_with_scope = [ln for ln in summary.split("\n") if "componentScope" in ln]
        assert len(lines_with_scope) > 0, "componentScope not found in summary"
        assert any(
            "(default)" in line for line in lines_with_scope
        ), f"Expected (default) in componentScope line, got: {lines_with_scope}"

    def test_warnings_section_shown_when_present(self) -> None:
        profile = BrandProfile(
            name="Acme",
            archetype="mobile-first",
            warnings=["Mobile-first with comprehensive scope is unusual"],
        )
        summary = render_gate_summary(profile)
        assert "Warnings" in summary
        assert "Mobile-first with comprehensive scope is unusual" in summary


# ─────────────────────────────────────────────────────────────
# Integration tests (require ANTHROPIC_API_KEY — excluded by default)
# ─────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_full_agent_enrichment_happy_path() -> None:
    from daf.agents.brand_discovery import run_brand_discovery

    profile = {
        "name": "Acme Corp",
        "archetype": "enterprise-b2b",
        "colors": {"primary": "#003366"},
    }
    result = run_brand_discovery(profile)
    assert isinstance(result, BrandProfile)
    assert result.accessibility == "AA"
    assert result.componentScope == "comprehensive"


@pytest.mark.integration
def test_agent_annotates_natural_language_color() -> None:
    from daf.agents.brand_discovery import run_brand_discovery

    profile = {
        "name": "X",
        "archetype": "enterprise-b2b",
        "colors": {"primary": "a deep ocean blue"},
    }
    result = run_brand_discovery(profile)
    assert isinstance(result, BrandProfile)
    assert result.colors is not None
    assert result.colors.primary == "a deep ocean blue"
