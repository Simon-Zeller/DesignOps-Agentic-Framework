"""ContrastSafePairer — CrewAI BaseTool.

Generates a comprehensive semantic token layer from the supplied palette and
validates WCAG 2.1 contrast ratios for all mandatory foreground/background
pairings. Fully deterministic: implements the WCAG relative luminance formula
with no external dependencies.
"""
from __future__ import annotations

import copy
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from daf.models import ContrastPairResult

# ---------------------------------------------------------------------------
# WCAG thresholds
# ---------------------------------------------------------------------------

WCAG_THRESHOLDS: dict[str, float] = {
    "AA":  4.5,
    "AAA": 7.0,
}

# ---------------------------------------------------------------------------
# Fixed-step semantic token rules per palette role
# Each entry: (semantic_token_name, preferred_tonal_step)
# The nearest available step is used when the preferred step is absent.
# ---------------------------------------------------------------------------

ROLE_SEMANTIC_MAP: dict[str, list[tuple[str, int]]] = {
    "neutral": [
        ("text.default",         950),
        ("text.subdued",         700),
        ("text.disabled",        400),
        ("text.placeholder",     500),
        ("text.inverse",          50),
        ("surface.default",       50),
        ("surface.elevated",     100),
        ("surface.overlay",      200),
        ("surface.sunken",       100),
        ("surface.inverse",      950),
        ("border.default",       200),
        ("border.strong",        400),
        ("border.subtle",        100),
        ("icon.default",         700),
        ("icon.subdued",         400),
        ("icon.disabled",        300),
        ("icon.inverse",          50),
    ],
    "primary": [
        ("interactive.primary.foreground",           50),
        ("interactive.primary.border",              700),
        ("interactive.primary.background-hover",    800),
        ("interactive.primary.background-active",   900),
        ("interactive.primary.background-disabled", 200),
        ("interactive.primary.text",                700),
        ("interactive.primary.text-hover",          800),
        ("text.link",                               700),
        ("text.link-hover",                         800),
        ("focus.ring",                              500),
    ],
    "accent": [
        ("interactive.accent.foreground",           50),
        ("interactive.accent.border",              700),
        ("interactive.accent.background-hover",    800),
        ("interactive.accent.background-active",   900),
        ("interactive.accent.background-disabled", 200),
        ("interactive.accent.text",                700),
    ],
    "secondary": [
        ("interactive.secondary.background",           700),
        ("interactive.secondary.foreground",            50),
        ("interactive.secondary.border",               700),
        ("interactive.secondary.background-hover",     800),
        ("interactive.secondary.background-active",    900),
        ("interactive.secondary.background-disabled",  200),
    ],
}

# ---------------------------------------------------------------------------
# Mandatory contrast pairings — these OVERRIDE the ROLE_SEMANTIC_MAP defaults
# with WCAG-validated alias selections.
# ---------------------------------------------------------------------------

MANDATORY_PAIRINGS = [
    # (semantic_token, palette_role, paired_against_hex_or_special)
    ("text.default",                   "neutral",  "bg_lightest"),
    ("text.inverse",                   "neutral",  "bg_darkest"),
    ("interactive.primary.background", "primary",  "#FFFFFF"),
    ("interactive.accent.background",  "accent",   "#FFFFFF"),
]

# ---------------------------------------------------------------------------
# Status tokens — generated once per profile, mapped to the best available role
# ---------------------------------------------------------------------------

_STATUS_CATEGORIES = ["success", "error", "warning", "info"]
_STATUS_STEPS: list[tuple[str, int]] = [
    ("background", 100),
    ("text",        900),
    ("border",      300),
]
_STATUS_ROLE_PRIORITY: dict[str, list[str]] = {
    "success": ["secondary", "accent", "primary", "neutral"],
    "error":   ["accent", "secondary", "primary", "neutral"],
    "warning": ["accent", "secondary", "primary", "neutral"],
    "info":    ["primary", "accent", "secondary", "neutral"],
}


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

class _ContrastSafePairerInput(BaseModel):
    palette: dict[str, str]
    accessibility: str = "AA"


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class ContrastSafePairer(BaseTool):
    """Select WCAG-safe semantic alias references and generate a full semantic token layer."""

    name: str = "contrast_safe_pairer"
    description: str = (
        "Generates a comprehensive semantic token layer from the supplied brand palette "
        "and validates WCAG 2.1 contrast ratios (AA=4.5:1, AAA=7:1) for all mandatory "
        "foreground/background pairings. Returns semantic_overrides dict (40+ entries for "
        "a typical 2-color profile) and a list of ContrastPairResult for critical pairs."
    )
    args_schema: type[BaseModel] = _ContrastSafePairerInput

    def _run(
        self,
        palette: dict[str, str],
        accessibility: str = "AA",
        **kwargs: Any,
    ) -> tuple[dict[str, str], list[ContrastPairResult]]:
        """Run the pairer.

        Returns a tuple of:
        - semantic_overrides: dict mapping semantic token name → global palette key
        - contrast_results: list of ContrastPairResult for each mandatory pairing
        """
        palette_snapshot = copy.deepcopy(palette)
        threshold = WCAG_THRESHOLDS.get(accessibility.upper(), WCAG_THRESHOLDS["AA"])
        semantic_overrides: dict[str, str] = {}
        contrast_results: list[ContrastPairResult] = []

        # ------------------------------------------------------------------
        # Pass 1: Generate semantic mappings from ROLE_SEMANTIC_MAP
        # ------------------------------------------------------------------
        for role, token_defs in ROLE_SEMANTIC_MAP.items():
            role_steps = self._steps_for_role(palette_snapshot, role)
            if not role_steps:
                continue
            available = sorted(role_steps.keys())
            for token_name, preferred_step in token_defs:
                nearest = self._nearest_step(preferred_step, available)
                semantic_overrides[token_name] = f"color.{role}.{nearest}"

        # ------------------------------------------------------------------
        # Pass 2: Validate and override mandatory contrast pairings
        # ------------------------------------------------------------------
        neutral_by_step = self._steps_for_role(palette_snapshot, "neutral")
        if neutral_by_step:
            avail_n = sorted(neutral_by_step.keys())
            lightest_neutral_hex = neutral_by_step[self._nearest_step(50, avail_n)]
            darkest_neutral_hex  = neutral_by_step[self._nearest_step(950, avail_n)]
        else:
            lightest_neutral_hex = "#FFFFFF"
            darkest_neutral_hex  = "#0A0A0A"

        for semantic_token, palette_role, bg_spec in MANDATORY_PAIRINGS:
            if bg_spec == "bg_lightest":
                bg_hex = lightest_neutral_hex
            elif bg_spec == "bg_darkest":
                bg_hex = darkest_neutral_hex
            else:
                bg_hex = bg_spec

            role_steps = self._steps_for_role(palette_snapshot, palette_role)
            if not role_steps:
                continue

            best_alias = ""
            best_ratio = 0.0
            best_passed = False

            # Iterate darkest-first to find the first passing step
            for step in sorted(role_steps.keys(), reverse=True):
                fg_hex = role_steps[step]
                ratio = self._wcag_contrast(fg_hex, bg_hex)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_alias = f"color.{palette_role}.{step}"
                if ratio >= threshold:
                    best_alias = f"color.{palette_role}.{step}"
                    best_ratio = ratio
                    best_passed = True
                    break

            semantic_overrides[semantic_token] = best_alias
            contrast_results.append(
                ContrastPairResult(
                    token_pair=(
                        f"{semantic_token} / "
                        f"{'surface.default' if bg_spec == 'bg_lightest' else ('text.default' if bg_spec == 'bg_darkest' else bg_hex)}"
                    ),
                    contrast_ratio=round(best_ratio, 2),
                    passed=best_passed,
                    alias_selected=best_alias,
                )
            )

        # ------------------------------------------------------------------
        # Pass 3: Generate status tokens using best available role per category
        # ------------------------------------------------------------------
        for category in _STATUS_CATEGORIES:
            chosen_role: str | None = None
            chosen_steps: dict[int, str] | None = None
            for role in _STATUS_ROLE_PRIORITY.get(category, ["primary", "neutral"]):
                role_steps = self._steps_for_role(palette_snapshot, role)
                if role_steps:
                    chosen_role = role
                    chosen_steps = role_steps
                    break
            if not chosen_role or not chosen_steps:
                continue
            available = sorted(chosen_steps.keys())
            for suffix, step in _STATUS_STEPS:
                nearest = self._nearest_step(step, available)
                semantic_overrides[f"status.{category}.{suffix}"] = (
                    f"color.{chosen_role}.{nearest}"
                )

        return semantic_overrides, contrast_results

    # ------------------------------------------------------------------
    # Public WCAG helpers (used directly in tests)
    # ------------------------------------------------------------------

    def _wcag_contrast(self, hex1: str, hex2: str) -> float:
        """Compute WCAG 2.1 contrast ratio between two hex colors."""
        l1 = self._relative_luminance(hex1)
        l2 = self._relative_luminance(hex2)
        lighter, darker = max(l1, l2), min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    def _relative_luminance(self, hex_color: str) -> float:
        """WCAG 2.1 relative luminance formula (sRGB linearisation)."""
        hex_color = hex_color.lstrip("#")
        r_srgb = int(hex_color[0:2], 16) / 255
        g_srgb = int(hex_color[2:4], 16) / 255
        b_srgb = int(hex_color[4:6], 16) / 255

        def linearize(c: float) -> float:
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        r = linearize(r_srgb)
        g = linearize(g_srgb)
        b = linearize(b_srgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _steps_for_role(
        self,
        palette: dict[str, str],
        role: str,
    ) -> dict[int, str]:
        """Return {step: hex} for all palette entries matching color.{role}.{step}."""
        result: dict[int, str] = {}
        prefix = f"color.{role}."
        for key, val in palette.items():
            if key.startswith(prefix):
                step_str = key[len(prefix):]
                if step_str.isdigit():
                    result[int(step_str)] = val
        return result

    def _nearest_step(self, target: int, available: list[int]) -> int:
        """Return the available tonal step closest to target."""
        return min(available, key=lambda s: abs(s - target))
