"""Tool: brand_profile_analyzer — extracts key fields from a brand-profile dict."""
from __future__ import annotations

from typing import Any


def analyze_brand_profile(profile_dict: dict[str, Any]) -> dict[str, Any]:
    """Extract archetype, a11y level, and modular scale from a brand profile.

    Args:
        profile_dict: The parsed brand-profile.json dict.

    Returns:
        A dict with keys: ``archetype``, ``a11y_level``, ``modular_scale``.
        Missing fields fall back to: ``"unspecified"``, ``"AA"``, ``None``.
    """
    return {
        "archetype": profile_dict.get("archetype", "unspecified") or "unspecified",
        "a11y_level": profile_dict.get("a11y_level", "AA") or "AA",
        "modular_scale": profile_dict.get("modular_scale"),
    }
