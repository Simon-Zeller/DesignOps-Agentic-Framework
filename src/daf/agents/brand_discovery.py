"""Brand Discovery Agent (Agent 1, DS Bootstrap Crew).

Validates, enriches, and completes a raw brand profile using four deterministic
tools plus LLM reasoning for natural language colour annotation and enrichment
narrative generation.
"""
from __future__ import annotations

import os
from typing import Any

from crewai import Agent, Crew, Task

from daf.models import BrandProfile
from daf.tools.archetype_resolver import ArchetypeResolver
from daf.tools.brand_profile_validator import BrandProfileSchemaValidator
from daf.tools.consistency_checker import ConsistencyChecker
from daf.tools.default_filler import DefaultFiller


def create_brand_discovery_agent() -> Agent:
    """Instantiate the Brand Discovery Agent (Tier 2 — Analytical, Claude Sonnet)."""
    model = os.environ.get("DAF_TIER2_MODEL", "claude-sonnet-4-20250514")
    return Agent(
        role="Brand Discovery Specialist",
        goal=(
            "Transform a raw brand profile into a validated, fully-enriched, §6-conformant "
            "brand-profile.json by running the four brand analysis tools in sequence, "
            "annotating natural language colour descriptions, and narrating what defaults "
            "were applied and why."
        ),
        backstory=(
            "You are a senior design systems architect with deep expertise in brand identity "
            "and design token engineering. You have reviewed hundreds of brand profiles and "
            "can instantly recognise contradictions, gaps, and archetype mismatches. "
            "Your analytical work is precise, structured, and always produces a complete, "
            "§6-conformant output that downstream crews can rely on without surprises."
        ),
        tools=[
            BrandProfileSchemaValidator(),
            ArchetypeResolver(),
            ConsistencyChecker(),
            DefaultFiller(),
        ],
        llm=model,
        verbose=False,
    )


def create_brand_discovery_task(raw_profile: dict[str, Any]) -> Task:
    """Create Task T1: validate → resolve → check → fill → return enriched BrandProfile."""
    profile_json = str(raw_profile)
    return Task(
        description=(
            f"Process the following raw brand profile and return an enriched BrandProfile.\n\n"
            f"Raw profile: {profile_json}\n\n"
            "Steps to follow IN ORDER:\n"
            "1. Run `brand_profile_schema_validator` with the raw profile dict. "
            "   If errors are returned, STOP and raise a ValueError listing all field errors.\n"
            "2. Run `archetype_resolver` with the archetype value from the profile. "
            "   Save the returned defaults dict.\n"
            "3. Run `consistency_checker` with the raw profile. "
            "   If any finding has severity='error', STOP and raise a ValueError with the findings.\n"
            "4. Run `default_filler` with (profile, archetype_defaults) from steps 1 and 2. "
            "   The returned dict is the enriched profile.\n"
            "5. Inspect all colour fields. If any value is a natural language description "
            "   (contains spaces, not a hex code), add a note in `_color_notes` explaining "
            "   your interpretation of the intended colour for the Token Foundation Agent.\n"
            "6. Return the enriched profile as a BrandProfile Pydantic model. "
            "   Include `_warnings` from ConsistencyChecker findings (warning severity) and "
            "   `_filled_fields` from DefaultFiller."
        ),
        expected_output=(
            "A fully-specified BrandProfile Pydantic model containing all §6 optional fields "
            "filled with archetype defaults where the user provided none, `_warnings` for any "
            "consistency findings, `_filled_fields` listing what was defaulted, and "
            "`_color_notes` for any natural language colour interpretations."
        ),
        output_pydantic=BrandProfile,
    )


def run_brand_discovery(raw_profile: dict[str, Any]) -> BrandProfile:
    """Run the Brand Discovery Agent and return a validated, enriched BrandProfile.

    Raises ValueError with structured error details on task failure.
    """
    agent = create_brand_discovery_agent()
    task = create_brand_discovery_task(raw_profile)
    task.agent = agent

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()

    # CrewAI kickoff may return CrewOutput or CrewStreamingOutput.
    # Access attributes defensively to satisfy type checker.
    pydantic_out = getattr(result, "pydantic", None)
    if pydantic_out is not None:
        return pydantic_out  # type: ignore[no-any-return]

    raw_out: str | None = getattr(result, "raw", None)
    if raw_out:
        try:
            import json

            data = json.loads(raw_out)
            return BrandProfile.model_validate(data)
        except Exception:
            pass

    raise ValueError(
        f"Brand Discovery Agent did not return a valid BrandProfile. "
        f"Raw output: {getattr(result, 'raw', repr(result))!r}"
    )
