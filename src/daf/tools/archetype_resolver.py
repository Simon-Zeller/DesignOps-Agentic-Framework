"""ArchetypeResolver — maps archetype names to complete §6 default dicts."""
from __future__ import annotations

import copy
from typing import Any

from crewai.tools import BaseTool

# ── Archetype defaults tables ─────────────────────────────────────────────────
# Every optional §6 field must have a non-None value for all five archetypes.

_DEFAULTS: dict[str, dict[str, Any]] = {
    "enterprise-b2b": {
        "colors": {
            "primary": "#003366",
            "secondary": "#336699",
            "accent": "#FF6600",
            "neutral": "#666666",
            "background": "#FFFFFF",
            "surface": "#F5F5F5",
            "text": "#1A1A1A",
        },
        "typography": {
            "scaleRatio": 1.25,
            "baseSize": 16,
        },
        "spacing": {
            "density": "compact",
            "baseUnit": 4,
        },
        "borderRadius": "subtle",
        "elevation": "moderate",
        "motion": "subtle",
        "themes": {
            "modes": ["light", "dark"],
            "brandOverrides": False,
        },
        "accessibility": "AA",
        "componentScope": "comprehensive",
        "breakpoints": {
            "strategy": "desktop-first",
        },
    },
    "consumer-b2c": {
        "colors": {
            "primary": "#FF4081",
            "secondary": "#448AFF",
            "accent": "#FF6D00",
            "neutral": "#757575",
            "background": "#FFFFFF",
            "surface": "#FAFAFA",
            "text": "#212121",
        },
        "typography": {
            "scaleRatio": 1.414,
            "baseSize": 16,
        },
        "spacing": {
            "density": "spacious",
            "baseUnit": 8,
        },
        "borderRadius": "rounded",
        "elevation": "pronounced",
        "motion": "expressive",
        "themes": {
            "modes": ["light", "dark"],
            "brandOverrides": False,
        },
        "accessibility": "AA",
        "componentScope": "standard",
        "breakpoints": {
            "strategy": "mobile-first",
        },
    },
    "mobile-first": {
        "colors": {
            "primary": "#1976D2",
            "secondary": "#388E3C",
            "accent": "#F57C00",
            "neutral": "#616161",
            "background": "#FFFFFF",
            "surface": "#F5F5F5",
            "text": "#212121",
        },
        "typography": {
            "scaleRatio": 1.2,
            "baseSize": 14,
        },
        "spacing": {
            "density": "compact",
            "baseUnit": 4,
        },
        "borderRadius": "rounded",
        "elevation": "flat",
        "motion": "subtle",
        "themes": {
            "modes": ["light", "dark"],
            "brandOverrides": False,
        },
        "accessibility": "AAA",
        "componentScope": "starter",
        "breakpoints": {
            "strategy": "mobile-first",
        },
    },
    "multi-brand": {
        "colors": {
            "primary": "#455A64",
            "secondary": "#78909C",
            "accent": "#00BCD4",
            "neutral": "#9E9E9E",
            "background": "#FFFFFF",
            "surface": "#F5F5F5",
            "text": "#263238",
        },
        "typography": {
            "scaleRatio": 1.25,
            "baseSize": 16,
        },
        "spacing": {
            "density": "standard",
            "baseUnit": 8,
        },
        "borderRadius": "moderate",
        "elevation": "moderate",
        "motion": "standard",
        "themes": {
            "modes": ["light", "dark", "high-contrast"],
            "brandOverrides": True,
        },
        "accessibility": "AA",
        "componentScope": "standard",
        "breakpoints": {
            "strategy": "mobile-first",
        },
    },
    "custom": {
        # Universal baseline: sensible defaults for bespoke projects
        "colors": {
            "primary": "#2196F3",
            "secondary": "#757575",
            "accent": "#FF9800",
            "neutral": "#9E9E9E",
            "background": "#FFFFFF",
            "surface": "#F5F5F5",
            "text": "#212121",
        },
        "typography": {
            "scaleRatio": 1.25,
            "baseSize": 16,
        },
        "spacing": {
            "density": "standard",
            "baseUnit": 8,
        },
        "borderRadius": "moderate",
        "elevation": "moderate",
        "motion": "standard",
        "themes": {
            "modes": ["light"],
            "brandOverrides": False,
        },
        "accessibility": "AA",
        "componentScope": "standard",
        "breakpoints": {
            "strategy": "mobile-first",
        },
    },
}


class ArchetypeResolver(BaseTool):
    """Returns the complete archetype defaults dict for a given archetype string.

    Returns a deep copy of the defaults so callers cannot mutate the source table.
    """

    name: str = "archetype_resolver"
    description: str = (
        "Given an archetype string ('enterprise-b2b', 'consumer-b2c', 'mobile-first', "
        "'multi-brand', or 'custom'), returns a complete dict of default values for all "
        "optional §6 brand profile fields."
    )

    def _run(self, archetype: str) -> dict[str, Any]:
        if archetype not in _DEFAULTS:
            raise ValueError(
                f"Unknown archetype '{archetype}'. "
                f"Must be one of: {', '.join(_DEFAULTS)}"
            )
        return copy.deepcopy(_DEFAULTS[archetype])
