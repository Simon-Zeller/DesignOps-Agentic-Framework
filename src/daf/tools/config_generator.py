"""ConfigGenerator — generates pipeline-config.json from a validated Brand Profile.

Agent 5 (Pipeline Configuration Agent) in the DS Bootstrap Crew uses this module
to produce the pipeline-config.json file that seeds all downstream crews (Phase 2–6).

All inference rules are deterministic mappings from Brand Profile fields.
No LLM reasoning is used in this module.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Inference rule tables (module-level constants)
# ---------------------------------------------------------------------------

_A11Y_SCORE_MAP: dict[str, int] = {
    "AA": 70,
    "AAA": 85,
}

_SCOPE_COVERAGE_MAP: dict[str, int] = {
    "starter": 80,
    "standard": 80,
    "comprehensive": 75,
}

_COMPREHENSIVE_BETA: list[str] = [
    "DatePicker",
    "DataGrid",
    "TreeView",
    "Drawer",
    "Stepper",
    "FileUpload",
    "RichText",
]

# Base categories always included; keyed by scope tier showing cumulative additions
_SCOPE_DOMAINS_MAP: dict[str, list[str]] = {
    "starter": ["forms", "layout", "feedback"],
    "standard": ["forms", "layout", "feedback", "navigation", "data-display"],
    "comprehensive": ["forms", "layout", "feedback", "navigation", "data-display", "data-entry"],
}

_DEFAULT_TIER1_MODEL = "claude-opus-4-20250514"
_DEFAULT_TIER2_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_TIER3_MODEL = "claude-haiku-4-20250414"


# ---------------------------------------------------------------------------
# Pure function
# ---------------------------------------------------------------------------

def generate_pipeline_config(brand_profile: dict, output_dir: str) -> str:
    """Generate pipeline-config.json from a validated Brand Profile.

    Args:
        brand_profile: Validated Brand Profile dict (must contain ``componentScope`` and
            ``accessibility`` keys).
        output_dir: Directory to write ``pipeline-config.json`` into.

    Returns:
        Absolute path to the written ``pipeline-config.json`` file.

    Raises:
        KeyError: If ``brand_profile`` is missing required top-level keys.
    """
    scope: str = brand_profile.get("componentScope") or brand_profile.get("scope", "starter")
    a11y_raw = brand_profile.get("accessibility", "AA")
    a11y_level: str = a11y_raw["level"] if isinstance(a11y_raw, dict) else str(a11y_raw)

    if scope not in _SCOPE_COVERAGE_MAP:
        raise ValueError(f"Unknown scope tier: {scope!r}")
    if a11y_level not in _A11Y_SCORE_MAP:
        raise ValueError(f"Unknown accessibility level: {a11y_level!r}")

    config: dict = {
        "qualityGates": {
            "a11yLevel": a11y_level,
            "minCompositeScore": _A11Y_SCORE_MAP[a11y_level],
            "minTestCoverage": _SCOPE_COVERAGE_MAP[scope],
            "blockOnWarnings": False,
        },
        "lifecycle": {
            "defaultStatus": "stable",
            "betaComponents": list(_COMPREHENSIVE_BETA) if scope == "comprehensive" else [],
            "deprecationGracePeriodDays": 90,
        },
        "domains": {
            "categories": list(_SCOPE_DOMAINS_MAP[scope]),
            "autoAssign": True,
        },
        "retry": {
            "maxComponentRetries": 3,
            "maxCrewRetries": 2,
        },
        "models": {
            "tier1": os.environ.get("DAF_TIER1_MODEL", _DEFAULT_TIER1_MODEL),
            "tier2": os.environ.get("DAF_TIER2_MODEL", _DEFAULT_TIER2_MODEL),
            "tier3": os.environ.get("DAF_TIER3_MODEL", _DEFAULT_TIER3_MODEL),
        },
        "buildConfig": {
            "tsTarget": "ES2020",
            "moduleFormat": "ESNext",
            "cssModules": False,
        },
    }

    out_path = Path(output_dir).resolve() / "pipeline-config.json"
    out_path.write_text(json.dumps(config, indent=2))
    return str(out_path)


# ---------------------------------------------------------------------------
# CrewAI BaseTool wrapper
# ---------------------------------------------------------------------------

class _ConfigGeneratorInput(BaseModel):
    brand_profile_json: str = Field(
        description="JSON string of the validated Brand Profile dict."
    )
    output_dir: str = Field(
        description="Directory path where pipeline-config.json will be written."
    )


class ConfigGenerator(BaseTool):
    """CrewAI tool that generates pipeline-config.json from a Brand Profile JSON string."""

    name: str = "ConfigGenerator"
    description: str = (
        "Generates pipeline-config.json by deriving quality gates, lifecycle settings, "
        "domain categories, retry limits, model tier identifiers, and build configuration "
        "from the validated Brand Profile. Returns the absolute path to the written file."
    )
    args_schema: type[BaseModel] = _ConfigGeneratorInput

    def _run(self, brand_profile_json: str, output_dir: str) -> str:
        brand_profile = json.loads(brand_profile_json)
        return generate_pipeline_config(brand_profile, output_dir)
