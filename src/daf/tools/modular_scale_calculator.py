"""ModularScaleCalculator — CrewAI BaseTool.

Computes typography, spacing, and supporting dimension scales from a brand
profile's dimension preferences. Fully deterministic: no LLM calls.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Named typography steps (16 steps from n=-7 to n=+8)
# Index 7 = n=0 = "base" (the brand's base font size)
# ---------------------------------------------------------------------------

FONT_SIZE_NAMES = [
    "6xs", "5xs", "4xs", "3xs", "2xs", "xs", "sm",
    "base",
    "lg", "xl", "2xl", "3xl", "4xl", "5xl", "6xl", "7xl",
]  # 16 names for n = -7..+8; "base" at index 7 → n=0

# Spacing steps: multipliers 1–12
SPACING_STEPS = list(range(1, 13))  # 1..12

# Elevation steps: 0–5
ELEVATION_STEPS = 6

# Border radius named steps
RADIUS_STEPS = ["none", "sm", "md", "lg", "xl", "full"]
RADIUS_VALUES_DEFAULT = ["0px", "2px", "4px", "8px", "16px", "9999px"]

# Opacity steps
OPACITY_STEPS = [0, 5, 10, 20, 40, 60, 80, 90, 95, 100]

# Motion duration steps (ms)
DURATION_STEPS = [50, 75, 100, 150, 200, 300, 400, 500]

# Easing curves
EASING_CURVES = {
    "linear":      "linear",
    "ease-in":     "cubic-bezier(0.4, 0, 1, 1)",
    "ease-out":    "cubic-bezier(0, 0, 0.2, 1)",
    "ease-in-out": "cubic-bezier(0.4, 0, 0.2, 1)",
    "spring":      "cubic-bezier(0.34, 1.56, 0.64, 1)",
}

# Density multipliers
DENSITY_MULTIPLIERS = {
    "compact":   0.75,
    "default":   1.0,
    "spacious":  1.33,
}

# ---------------------------------------------------------------------------
# Archetype defaults
# ---------------------------------------------------------------------------

ARCHETYPE_DEFAULTS: dict[str, dict[str, Any]] = {
    "enterprise-b2b": {
        "typography": {"baseSize": 16, "scaleRatio": 1.25},
        "spacing":    {"baseUnit": 4, "density": "default"},
    },
    "consumer-b2c": {
        "typography": {"baseSize": 16, "scaleRatio": 1.333},
        "spacing":    {"baseUnit": 4, "density": "default"},
    },
    "marketplace": {
        "typography": {"baseSize": 16, "scaleRatio": 1.25},
        "spacing":    {"baseUnit": 4, "density": "default"},
    },
    "creative-studio": {
        "typography": {"baseSize": 18, "scaleRatio": 1.414},
        "spacing":    {"baseUnit": 8, "density": "spacious"},
    },
    "multi-brand": {
        "typography": {"baseSize": 16, "scaleRatio": 1.25},
        "spacing":    {"baseUnit": 4, "density": "default"},
    },
}

_DEFAULT_ARCHETYPE_FALLBACK = ARCHETYPE_DEFAULTS["enterprise-b2b"]


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

class _ModularScaleInput(BaseModel):
    typography: dict[str, Any] | None = None
    spacing: dict[str, Any] | None = None
    archetype: str = "enterprise-b2b"


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class ModularScaleCalculator(BaseTool):
    """Compute typography, spacing, and supporting dimension token scales."""

    name: str = "modular_scale_calculator"
    description: str = (
        "Compute a complete set of dimension token scales from brand profile typography "
        "and spacing settings: font-size (16 steps), spacing (12 steps), elevation (6), "
        "radius (6), opacity (10), duration (8), easing (5). Returns a flat dict of "
        "'scale.{category}.{step}' tokens."
    )
    args_schema: type[BaseModel] = _ModularScaleInput

    def _run(
        self,
        typography: dict[str, Any] | None = None,
        spacing: dict[str, Any] | None = None,
        archetype: str = "enterprise-b2b",
        **kwargs: Any,
    ) -> dict[str, str]:
        """Run the scale calculator and return flat token dict."""
        defaults = ARCHETYPE_DEFAULTS.get(archetype, _DEFAULT_ARCHETYPE_FALLBACK)

        # Merge typography with defaults
        typo = {**defaults["typography"], **(typography or {})}
        spc = {**defaults["spacing"], **(spacing or {})}

        base_size: float = float(typo.get("baseSize") or defaults["typography"]["baseSize"])
        scale_ratio: float = float(typo.get("scaleRatio") or defaults["typography"]["scaleRatio"])
        base_unit: int = int(spc.get("baseUnit") or defaults["spacing"]["baseUnit"])
        density: str = str(spc.get("density") or defaults["spacing"]["density"]).lower()
        density_mult: float = DENSITY_MULTIPLIERS.get(density, 1.0)

        result: dict[str, str] = {}

        # 1. Font-size: 16 steps, n = -7..+8
        for i, name in enumerate(FONT_SIZE_NAMES):
            n = i - 7  # maps index 0 → n=-7, index 5 (base) → n=0
            value_px = base_size * (scale_ratio ** n)
            result[f"scale.font-size.{name}"] = f"{round(value_px)}px"

        # 2. Spacing: 12 steps (1×–12× baseUnit × density)
        for step in SPACING_STEPS:
            value_px = round(step * base_unit * density_mult)
            result[f"scale.spacing.{step}"] = f"{value_px}px"

        # 3. Elevation: 6 shadows (increasing depth)
        elevations = [
            "none",
            "0 1px 2px rgba(0,0,0,0.05)",
            "0 2px 4px rgba(0,0,0,0.10)",
            "0 4px 8px rgba(0,0,0,0.12)",
            "0 8px 16px rgba(0,0,0,0.15)",
            "0 16px 32px rgba(0,0,0,0.18)",
        ]
        for i, shadow_val in enumerate(elevations):
            result[f"scale.elevation.{i}"] = shadow_val

        # 4. Border radius: 6 named steps
        for name, val in zip(RADIUS_STEPS, RADIUS_VALUES_DEFAULT):
            result[f"scale.radius.{name}"] = val

        # 5. Opacity: 10 steps
        for pct in OPACITY_STEPS:
            result[f"scale.opacity.{pct}"] = f"{pct}%"

        # 6. Duration: 8 steps
        for ms in DURATION_STEPS:
            result[f"scale.duration.{ms}"] = f"{ms}ms"

        # 7. Easing: 5 curves
        for name, curve in EASING_CURVES.items():
            result[f"scale.easing.{name}"] = curve

        return result
