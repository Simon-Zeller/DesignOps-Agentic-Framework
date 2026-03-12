"""Unit tests for TokenFoundationAgent (Task T2) — TDD red phase stubs."""
from __future__ import annotations

import json


import pytest


@pytest.fixture
def brand_profile_fixture():
    """Minimal enterprise BrandProfile fixture for task T2 tests."""
    from daf.models import BrandProfile

    return BrandProfile(
        name="Acme Corp",
        archetype="enterprise-b2b",
        colors={"primary": "#3D72B4", "neutral": "#95A5A6"},
        typography={"baseSize": 16, "scaleRatio": 1.25},
        spacing={"baseUnit": 4, "density": "default"},
        accessibility="AA",
        themes={"modes": ["light", "dark"]},
    )


@pytest.fixture
def aaa_brand_profile_fixture():
    """AAA accessibility profile for contrast pair tests."""
    from daf.models import BrandProfile

    return BrandProfile(
        name="Apex Enterprise",
        archetype="enterprise-b2b",
        colors={"primary": "#1A3A6B", "neutral": "#5A6A7A"},
        typography={"baseSize": 16, "scaleRatio": 1.25},
        spacing={"baseUnit": 4, "density": "default"},
        accessibility="AAA",
        themes={"modes": ["light"]},
    )


@pytest.fixture
def multi_brand_profile_fixture():
    """Multi-brand profile for brand override file tests."""
    from daf.models import BrandProfile

    return BrandProfile(
        name="MultiCo",
        archetype="multi-brand",
        colors={"primary": "#E74C3C", "neutral": "#95A5A6"},
        typography={"baseSize": 16, "scaleRatio": 1.25},
        spacing={"baseUnit": 4, "density": "default"},
        accessibility="AA",
        themes={"modes": ["light"], "brandOverrides": True, "brands": ["brand-a", "brand-b"]},
    )


def test_task_output_lists_three_written_files(tmp_path, brand_profile_fixture):
    """TokenFoundationOutput.written_files has 3 paths, all existing and valid JSON."""
    from daf.tools.color_palette_generator import ColorPaletteGenerator
    from daf.tools.contrast_safe_pairer import ContrastSafePairer
    from daf.tools.dtcg_formatter import WC3DTCGFormatter
    from daf.tools.modular_scale_calculator import ModularScaleCalculator

    profile = brand_profile_fixture
    colors_dict = {
        k: v
        for k, v in (profile.colors.model_dump() if profile.colors else {}).items()
        if v is not None
    }
    color_notes = profile.color_notes or {}
    palette = ColorPaletteGenerator()._run(colors=colors_dict, color_notes=color_notes)

    typo = profile.typography.model_dump() if profile.typography else None
    spacing = profile.spacing.model_dump() if profile.spacing else None
    scales = ModularScaleCalculator()._run(
        typography=typo, spacing=spacing, archetype=profile.archetype
    )

    overrides, contrast_results = ContrastSafePairer()._run(
        palette=palette, accessibility=profile.accessibility or "AA"
    )

    written_files = WC3DTCGFormatter()._run(
        global_palette=palette,
        scale_tokens=scales,
        semantic_overrides=overrides,
        component_overrides={},
        themes=profile.themes.modes if profile.themes and profile.themes.modes else [],
        brands={},
        output_dir=str(tmp_path),
    )

    assert len(written_files) == 3
    for path in written_files:
        assert (tmp_path / "tokens" / path.split("/tokens/")[-1]).exists() or __import__("os").path.exists(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)


def test_token_counts_in_expected_range(tmp_path, brand_profile_fixture):
    """Token counts per tier fall within expected ranges."""
    from daf.tools.color_palette_generator import ColorPaletteGenerator
    from daf.tools.contrast_safe_pairer import ContrastSafePairer
    from daf.tools.dtcg_formatter import WC3DTCGFormatter
    from daf.tools.modular_scale_calculator import ModularScaleCalculator

    profile = brand_profile_fixture
    colors_dict = {k: v for k, v in (profile.colors.model_dump() if profile.colors else {}).items() if v is not None}
    palette = ColorPaletteGenerator()._run(colors=colors_dict, color_notes=profile.color_notes or {})
    scales = ModularScaleCalculator()._run(
        typography=profile.typography.model_dump() if profile.typography else None,
        spacing=profile.spacing.model_dump() if profile.spacing else None,
        archetype=profile.archetype,
    )
    overrides, _ = ContrastSafePairer()._run(palette=palette, accessibility=profile.accessibility or "AA")
    written_files = WC3DTCGFormatter()._run(
        global_palette=palette,
        scale_tokens=scales,
        semantic_overrides=overrides,
        component_overrides={},
        themes=[],
        brands={},
        output_dir=str(tmp_path),
    )

    def _count_tokens(data: dict) -> int:
        count = 0
        for key, val in data.items():
            if isinstance(val, dict):
                if "$value" in val:
                    count += 1
                else:
                    count += _count_tokens(val)
        return count

    base_path = next(p for p in written_files if "base" in p)
    semantic_path = next(p for p in written_files if "semantic" in p)
    component_path = next(p for p in written_files if "component" in p)

    with open(base_path) as f:
        base_count = _count_tokens(json.load(f))
    with open(semantic_path) as f:
        semantic_count = _count_tokens(json.load(f))
    with open(component_path) as f:
        component_data = json.load(f)
        component_count = _count_tokens(component_data) if component_data else 0

    assert 70 <= base_count <= 600, f"base token count {base_count} out of range [70, 600]"
    assert 40 <= semantic_count <= 200, f"semantic token count {semantic_count} out of range [40, 200]"
    assert 0 <= component_count <= 100, f"component token count {component_count} out of range [0, 100]"


def test_aaa_profile_contrast_pairs_all_pass(tmp_path, aaa_brand_profile_fixture):
    """AAA accessibility profile: all contrast pairs have passed=True."""
    from daf.tools.color_palette_generator import ColorPaletteGenerator
    from daf.tools.contrast_safe_pairer import ContrastSafePairer

    profile = aaa_brand_profile_fixture
    colors_dict = {k: v for k, v in (profile.colors.model_dump() if profile.colors else {}).items() if v is not None}
    palette = ColorPaletteGenerator()._run(colors=colors_dict, color_notes={})
    _, contrast_results = ContrastSafePairer()._run(palette=palette, accessibility="AAA")

    for pair in contrast_results:
        assert pair.passed, (
            f"Pair {pair.token_pair!r} failed AAA: ratio={pair.contrast_ratio:.2f}, "
            f"alias={pair.alias_selected!r}"
        )


def test_multi_brand_profile_writes_5_files(tmp_path, multi_brand_profile_fixture):
    """Multi-brand profile generates 3 base files + 2 brand override files = 5 total."""
    from daf.tools.color_palette_generator import ColorPaletteGenerator
    from daf.tools.contrast_safe_pairer import ContrastSafePairer
    from daf.tools.dtcg_formatter import WC3DTCGFormatter
    from daf.tools.modular_scale_calculator import ModularScaleCalculator

    profile = multi_brand_profile_fixture
    colors_dict = {k: v for k, v in (profile.colors.model_dump() if profile.colors else {}).items() if v is not None}
    palette = ColorPaletteGenerator()._run(colors=colors_dict, color_notes={})
    scales = ModularScaleCalculator()._run(
        typography=profile.typography.model_dump() if profile.typography else None,
        spacing=profile.spacing.model_dump() if profile.spacing else None,
        archetype=profile.archetype,
    )
    overrides, _ = ContrastSafePairer()._run(palette=palette, accessibility=profile.accessibility or "AA")

    brand_names = getattr(profile.themes, "brands", None) or []
    brands = {brand: {"interactive.primary.background": f"color.primary.{700 + i * 100}"} for i, brand in enumerate(brand_names)}

    written_files = WC3DTCGFormatter()._run(
        global_palette=palette,
        scale_tokens=scales,
        semantic_overrides=overrides,
        component_overrides={},
        themes=profile.themes.modes if profile.themes and profile.themes.modes else [],
        brands=brands,
        output_dir=str(tmp_path),
    )

    assert len(written_files) == 5, f"Expected 5 files for multi-brand, got {len(written_files)}: {written_files}"


@pytest.mark.integration
def test_integration_task_t2_with_live_llm(tmp_path):
    """Integration test: full Task T2 run with live Anthropic API. Requires ANTHROPIC_API_KEY."""
    import os

    from daf.agents.token_foundation import create_token_foundation_agent, create_token_foundation_task
    from daf.models import BrandProfile

    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    profile = BrandProfile(
        name="Integration Test Corp",
        archetype="enterprise-b2b",
        colors={"primary": "#3D72B4", "neutral": "#95A5A6"},
        typography={"baseSize": 16, "scaleRatio": 1.25},
        spacing={"baseUnit": 4, "density": "default"},
        accessibility="AA",
    )

    from crewai import Crew

    agent = create_token_foundation_agent()
    task = create_token_foundation_task(profile=profile, output_dir=str(tmp_path))
    task.agent = agent

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()

    pydantic_out = getattr(result, "pydantic", None)
    assert pydantic_out is not None
    assert len(pydantic_out.written_files) >= 3
