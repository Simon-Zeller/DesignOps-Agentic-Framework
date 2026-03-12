"""Token Foundation Agent (Agent 2, DS Bootstrap Crew).

Transforms an enriched BrandProfile into three W3C DTCG token files by
running four deterministic tools in sequence via Task T2.
"""
from __future__ import annotations

import os
from typing import Any

from crewai import Agent, Task

from daf.models import BrandProfile, TokenFoundationOutput
from daf.tools.color_palette_generator import ColorPaletteGenerator
from daf.tools.contrast_safe_pairer import ContrastSafePairer
from daf.tools.dtcg_formatter import WC3DTCGFormatter
from daf.tools.modular_scale_calculator import ModularScaleCalculator


def create_token_foundation_agent() -> Agent:
    """Instantiate the Token Foundation Agent (Tier 2 — Analytical, Claude Sonnet)."""
    model = os.environ.get("DAF_TIER2_MODEL", "claude-sonnet-4-20250514")
    return Agent(
        role="Token Foundation Specialist",
        goal=(
            "Transform the enriched BrandProfile from Agent 1 into a complete, "
            "contrast-safe, W3C DTCG-conformant token set — three tier files in tokens/ — "
            "using the four token tools in strict sequence: ColorPaletteGenerator, "
            "ModularScaleCalculator, ContrastSafePairer, WC3DTCGFormatter. "
            "Return a TokenFoundationOutput summarising written files, token counts, "
            "and contrast pair results."
        ),
        backstory=(
            "You are a senior design token engineer who has built foundational token systems "
            "for dozens of large enterprise design systems. You understand the W3C DTCG "
            "specification deeply — the three-tier separation of global, semantic, and "
            "component tokens, DTCG reference syntax, and $type conventions. "
            "Your job is to synthesise a harmonious, contrast-safe initial token set from "
            "the brand intent captured in the BrandProfile, and to produce it in a rigorous, "
            "machine-readable format that the Token Validation Agent can audit with confidence."
        ),
        tools=[
            ColorPaletteGenerator(),
            ModularScaleCalculator(),
            ContrastSafePairer(),
            WC3DTCGFormatter(),
        ],
        llm=model,
        verbose=False,
    )


def create_token_foundation_task(
    profile: BrandProfile,
    output_dir: str,
    context_tasks: list[Task] | None = None,
) -> Task:
    """Create Task T2: generate the three DTCG token files from an enriched BrandProfile.

    Args:
        profile: Enriched BrandProfile from Task T1.
        output_dir: Base directory under which tokens/ will be created.
        context_tasks: Optional list of upstream Task objects (e.g. [task_t1]).
    """
    profile_summary = _profile_summary(profile)
    colors_dict = _colors_dict(profile)
    color_notes = profile.color_notes or {}
    accessibility = profile.accessibility or "AA"
    themes_modes = (profile.themes.modes if profile.themes and profile.themes.modes else [])
    is_multi_brand = (
        profile.archetype == "multi-brand"
        and profile.themes is not None
        and getattr(profile.themes, "brandOverrides", False)
    )
    brand_names = getattr(profile.themes, "brands", None) or [] if profile.themes else []

    description = (
        f"Run Task T2: Token Foundation for brand '{profile.name}' "
        f"(archetype: {profile.archetype}, accessibility: {accessibility}).\n\n"
        f"Brand profile summary:\n{profile_summary}\n\n"
        f"Execute the four tools IN ORDER:\n\n"
        f"STEP 1 — Run `color_palette_generator` with:\n"
        f"  colors = {colors_dict}\n"
        f"  color_notes = {color_notes}\n"
        f"  → produces global-tier color tokens (color.{{role}}.{{step}})\n\n"
        f"STEP 2 — Run `modular_scale_calculator` with:\n"
        f"  typography = {_typo_dict(profile)}\n"
        f"  spacing = {_spacing_dict(profile)}\n"
        f"  archetype = '{profile.archetype}'\n"
        f"  → produces global-tier dimension tokens (scale.*)\n\n"
        f"STEP 3 — Run `contrast_safe_pairer` with:\n"
        f"  palette = <output from step 1>\n"
        f"  accessibility = '{accessibility}'\n"
        f"  → produces semantic alias overrides dict and contrast_results list\n\n"
        f"STEP 4 — Run `wc3_dtcg_formatter` with:\n"
        f"  global_palette = <output from step 1>\n"
        f"  scale_tokens = <output from step 2>\n"
        f"  semantic_overrides = <overrides dict from step 3>\n"
        f"  component_overrides = {{}}\n"
        f"  themes = {themes_modes}\n"
        f"  brands = {_brands_dict(brand_names, colors_dict) if is_multi_brand else {}}\n"
        f"  output_dir = '{output_dir}'\n"
        f"  → writes tokens/base.tokens.json, tokens/semantic.tokens.json, "
        f"tokens/component.tokens.json (and tokens/brands/*.tokens.json for multi-brand)\n\n"
        f"RETURN a TokenFoundationOutput with:\n"
        f"  written_files: list of absolute file paths from step 4\n"
        f"  token_counts: {{'base': <count>, 'semantic': <count>, 'component': <count>}}\n"
        f"  contrast_pairs: list of ContrastPairResult from step 3\n"
        f"  token_notes: brief notes on any adjustments made for contrast compliance"
    )

    task_kwargs: dict[str, Any] = dict(
        description=description,
        expected_output=(
            "A TokenFoundationOutput Pydantic model with: "
            "written_files (list of absolute paths to the 3+ DTCG JSON files written to tokens/), "
            "token_counts (dict with 'base', 'semantic', 'component' keys), "
            "contrast_pairs (list of ContrastPairResult records), "
            "and token_notes (string or None)."
        ),
        output_pydantic=TokenFoundationOutput,
    )
    if context_tasks:
        task_kwargs["context"] = context_tasks

    return Task(**task_kwargs)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _profile_summary(profile: BrandProfile) -> str:
    parts = [
        f"  name: {profile.name}",
        f"  archetype: {profile.archetype}",
        f"  accessibility: {profile.accessibility or 'AA'}",
        f"  themes: {profile.themes.modes if profile.themes else None}",
    ]
    if profile.colors:
        for role, val in profile.colors.model_dump().items():
            if val is not None:
                parts.append(f"  colors.{role}: {val}")
    if profile.color_notes:
        parts.append(f"  _color_notes present: {list(profile.color_notes.keys())}")
    return "\n".join(parts)


def _colors_dict(profile: BrandProfile) -> dict[str, str]:
    if not profile.colors:
        return {}
    return {
        k: v
        for k, v in profile.colors.model_dump().items()
        if v is not None
    }


def _typo_dict(profile: BrandProfile) -> dict[str, Any] | None:
    if not profile.typography:
        return None
    return {k: v for k, v in profile.typography.model_dump().items() if v is not None}


def _spacing_dict(profile: BrandProfile) -> dict[str, Any] | None:
    if not profile.spacing:
        return None
    return {k: v for k, v in profile.spacing.model_dump().items() if v is not None}


def _brands_dict(brand_names: list[str], colors: dict[str, str]) -> dict[str, dict[str, str]]:
    """Build minimal per-brand override dict using brand-specific primary aliases."""
    result: dict[str, dict[str, str]] = {}
    steps = [500, 600, 700, 800]
    for i, name in enumerate(brand_names):
        result[name] = {
            "interactive.primary.background": f"color.primary.{steps[i % len(steps)]}",
        }
    return result
