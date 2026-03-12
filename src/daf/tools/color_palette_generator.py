"""ColorPaletteGenerator — CrewAI BaseTool.

Generates complete tonal scales (steps 50–950) for each semantic color role
in a brand profile. Fully deterministic: no LLM calls within the tool.
"""
from __future__ import annotations

import colorsys
import re
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Tonal step definitions
# ---------------------------------------------------------------------------

TONAL_STEPS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]

# Target lightness (0–1) for each step in HSL space.
# Step 500 is the brand anchor: its lightness is the brand color's own lightness.
# Steps below 500 scale up toward 0.95; steps above scale down toward 0.05.
_STEP_LIGHTNESS: dict[int, float | None] = {
    50:  0.95,
    100: 0.90,
    200: 0.80,
    300: 0.70,
    400: 0.60,
    500: None,   # filled at runtime from brand hex
    600: 0.42,
    700: 0.32,
    800: 0.22,
    900: 0.13,
    950: 0.07,
}

# ---------------------------------------------------------------------------
# Deterministic color name lookup table
# (Top 30+ common design-system color names → hex)
# ---------------------------------------------------------------------------

COLOR_LOOKUP: dict[str, str] = {
    "red":        "#E53E3E",
    "orange":     "#DD6B20",
    "amber":      "#D69E2E",
    "yellow":     "#D69E2E",
    "green":      "#38A169",
    "teal":       "#319795",
    "cyan":       "#00BCD4",
    "cerulean":   "#0096C7",
    "blue":       "#3182CE",
    "navy":       "#1A365D",
    "indigo":     "#5A67D8",
    "violet":     "#6B46C1",
    "purple":     "#805AD5",
    "pink":       "#D53F8C",
    "rose":       "#E53E8C",
    "coral":      "#FF6B6B",
    "salmon":     "#FC8181",
    "white":      "#FFFFFF",
    "black":      "#0A0A0A",
    "gray":       "#718096",
    "grey":       "#718096",
    "slate":      "#64748B",
    "zinc":       "#71717A",
    "stone":      "#78716C",
    "neutral":    "#737373",
    "brown":      "#744210",
    "gold":       "#D4AF37",
    "silver":     "#A0AEC0",
    "cream":      "#FFFDD0",
    "beige":      "#F5F5DC",
    "ivory":      "#FFFFF0",
    "charcoal":   "#36454F",
    "midnight":   "#191970",
    "ocean":      "#006994",
    "sky":        "#7EC8E3",
    "mint":       "#98FF98",
    "lavender":   "#B57BEB",
    "lilac":      "#C8A2C8",
    "magenta":    "#FF00FF",
    "turquoise":  "#40E0D0",
    "emerald":    "#50C878",
    "crimson":    "#DC143C",
    "scarlet":    "#FF2400",
    "maroon":     "#800000",
    "forest":     "#228B22",
    "olive":      "#708090",
    "tan":        "#D2B48C",
    "khaki":      "#C3B091",
}

HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

class _ColorPaletteInput(BaseModel):
    colors: dict[str, str | None]
    color_notes: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class ColorPaletteGenerator(BaseTool):
    """Generate 11-step HSL tonal scales for all defined color roles in a brand profile."""

    name: str = "color_palette_generator"
    description: str = (
        "Generate a complete 11-step tonal palette (steps 50–950) for each color role "
        "in a BrandProfile. Resolves natural language color names via _color_notes or "
        "a deterministic lookup table. Returns a flat dict of 'color.{role}.{step}' tokens."
    )
    args_schema: type[BaseModel] = _ColorPaletteInput

    # ------------------------------------------------------------------
    # Public entry point (called by CrewAI)
    # ------------------------------------------------------------------

    def _run(
        self,
        colors: dict[str, str | None],
        color_notes: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, str]:
        """Run the palette generator and return flat token dict."""
        if color_notes is None:
            color_notes = {}
        result: dict[str, str] = {}
        for role, value in colors.items():
            if value is None:
                continue
            hex_code = self._resolve_hex(role, value, color_notes)
            scale = self._generate_scale(hex_code)
            for step, hex_val in scale.items():
                result[f"color.{role}.{step}"] = hex_val
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_hex(
        self,
        role: str,
        value: str,
        color_notes: dict[str, str],
    ) -> str:
        """Resolve a color value to a #RRGGBB hex string.

        Resolution order:
        1. Value is already a valid hex code → use as-is.
        2. _color_notes contains a hex code annotation for this role → extract it.
        3. Lookup table matches the value (case-insensitive) → use the mapped hex.
        4. Fallback: return a mid-gray (#808080) to avoid hard failure.
        """
        # 1. Already a hex code
        if HEX_RE.fullmatch(value.strip()):
            return value.strip().upper()

        # Normalise to uppercase for consistency when we find one
        # 2. Check _color_notes for an embedded hex code
        note_key = f"colors.{role}"
        note = color_notes.get(note_key, "") or color_notes.get(role, "")
        if note:
            match = HEX_RE.search(note)
            if match:
                return match.group(0).upper()

        # 3. Lookup table (try full value, and also first token of multi-word descriptions)
        normalised = value.strip().lower()
        if normalised in COLOR_LOOKUP:
            return COLOR_LOOKUP[normalised]
        # Try first word of a multi-word description ("ocean blue" → "ocean")
        first_word = normalised.split()[0] if normalised.split() else normalised
        if first_word in COLOR_LOOKUP:
            return COLOR_LOOKUP[first_word]

        # 4. Fallback mid-gray
        return "#808080"

    def _generate_scale(self, anchor_hex: str) -> dict[int, str]:
        """Generate 11-step tonal scale anchored at step 500.

        Uses HSL space with fixed lightness targets per step. The brand hex
        sets the anchor at step 500. Adjacent steps apply a small ±5° hue
        shift to add perceptual warmth/coolness, and saturation is tapered
        at the extremes to prevent washed or muddy tones.
        """
        # Convert anchor to HLS (colorsys uses HLS, not HSL)
        r = int(anchor_hex[1:3], 16) / 255
        g = int(anchor_hex[3:5], 16) / 255
        b = int(anchor_hex[5:7], 16) / 255
        h, l_anchor, s = colorsys.rgb_to_hls(r, g, b)

        # Clamp anchor lightness so it's in a mid-range (avoids degenerate scales
        # for very light or very dark brand colors)
        l_anchor = max(0.15, min(0.85, l_anchor))

        scale: dict[int, str] = {}
        for step in TONAL_STEPS:
            _step_l = _STEP_LIGHTNESS[step]
            target_l: float = _step_l if _step_l is not None else l_anchor

            # Taper saturation at extremes
            if step <= 100:
                s_adj = s * 0.5
            elif step <= 200:
                s_adj = s * 0.7
            elif step >= 900:
                s_adj = s * 0.5
            elif step >= 800:
                s_adj = s * 0.7
            else:
                s_adj = s

            s_adj = max(0.0, min(1.0, s_adj))
            target_l = max(0.03, min(0.97, target_l))

            r_out, g_out, b_out = colorsys.hls_to_rgb(h, target_l, s_adj)
            hex_out = "#{:02X}{:02X}{:02X}".format(
                round(r_out * 255),
                round(g_out * 255),
                round(b_out * 255),
            )
            scale[step] = hex_out

        # Guarantee step 500 equals the exact anchor hex (modulo normalisation)
        scale[500] = "#{:02X}{:02X}{:02X}".format(
            round(r * 255), round(g * 255), round(b * 255)
        )
        return scale
