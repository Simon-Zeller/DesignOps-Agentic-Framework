"""Archetype defaults map for the DAF brand interview.

Keyed by archetype enum value. Each entry provides default values for all
optional §6 brand profile fields shown during the 11-step interview.
"""
from typing import Any

ARCHETYPE_DEFAULTS: dict[str, dict[str, Any]] = {
    "enterprise-b2b": {
        "colors": {
            "primary": "#1a73e8",
            "secondary": "#5f6368",
            "neutral": "#f1f3f4",
            "semantic": {
                "success": "#34a853",
                "warning": "#fbbc04",
                "error": "#ea4335",
                "info": "#4285f4",
            },
        },
        "typography": {
            "scaleRatio": 1.25,
            "baseSize": 16,
        },
        "spacing": {"density": "compact", "baseUnit": 4},
        "borderRadius": "subtle",
        "elevation": "moderate",
        "motion": "subtle",
        "themes": ["light", "dark"],
        "accessibility": "AA",
        "componentScope": "comprehensive",
        "breakpoints": {
            "sm": "640px",
            "md": "768px",
            "lg": "1024px",
            "xl": "1280px",
        },
    },
    "consumer-b2c": {
        "colors": {
            "primary": "#e91e63",
            "secondary": "#ff9800",
            "neutral": "#fafafa",
            "semantic": {
                "success": "#4caf50",
                "warning": "#ff9800",
                "error": "#f44336",
                "info": "#2196f3",
            },
        },
        "typography": {
            "scaleRatio": 1.414,
            "baseSize": 16,
        },
        "spacing": {"density": "spacious", "baseUnit": 8},
        "borderRadius": "rounded",
        "elevation": "pronounced",
        "motion": "expressive",
        "themes": ["light", "dark"],
        "accessibility": "AA",
        "componentScope": "standard",
        "breakpoints": {
            "sm": "480px",
            "md": "768px",
            "lg": "1024px",
            "xl": "1440px",
        },
    },
    "mobile-first": {
        "colors": {
            "primary": "#6200ee",
            "secondary": "#03dac6",
            "neutral": "#f5f5f5",
            "semantic": {
                "success": "#4caf50",
                "warning": "#ff9800",
                "error": "#b00020",
                "info": "#0288d1",
            },
        },
        "typography": {
            "scaleRatio": 1.2,
            "baseSize": 14,
        },
        "spacing": {"density": "compact", "baseUnit": 4},
        "borderRadius": "rounded",
        "elevation": "flat",
        "motion": "subtle",
        "themes": ["light", "dark"],
        "accessibility": "AAA",
        "componentScope": "starter",
        "breakpoints": {
            "sm": "360px",
            "md": "480px",
            "lg": "768px",
            "xl": "1024px",
        },
    },
    "multi-brand": {
        "colors": {
            "primary": "#007bff",
            "secondary": "#6c757d",
            "neutral": "#f8f9fa",
            "semantic": {
                "success": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "info": "#17a2b8",
            },
        },
        "typography": {
            "scaleRatio": 1.25,
            "baseSize": 16,
        },
        "spacing": {"density": "standard", "baseUnit": 8},
        "borderRadius": "moderate",
        "elevation": "moderate",
        "motion": "standard",
        "themes": ["light", "dark", "high-contrast"],
        "accessibility": "AA",
        "componentScope": "standard",
        "breakpoints": {
            "sm": "576px",
            "md": "768px",
            "lg": "992px",
            "xl": "1200px",
        },
    },
    "custom": {
        "colors": {
            "primary": "#000000",
            "secondary": "#666666",
            "neutral": "#f0f0f0",
            "semantic": {
                "success": "#008000",
                "warning": "#ffa500",
                "error": "#ff0000",
                "info": "#0000ff",
            },
        },
        "typography": {
            "scaleRatio": 1.25,
            "baseSize": 16,
        },
        "spacing": {"density": "standard", "baseUnit": 8},
        "borderRadius": "moderate",
        "elevation": "moderate",
        "motion": "standard",
        "themes": ["light"],
        "accessibility": "AA",
        "componentScope": "standard",
        "breakpoints": {
            "sm": "640px",
            "md": "768px",
            "lg": "1024px",
            "xl": "1280px",
        },
    },
}
