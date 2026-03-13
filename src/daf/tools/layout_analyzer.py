"""Layout Analyzer — extracts layout model, spacing rhythm, and breakpoint config from spec."""
from __future__ import annotations

from typing import Any

_DEFAULTS = {"model": "flex", "direction": "row", "align": "stretch"}


def extract_layout(spec: dict[str, Any]) -> dict[str, Any]:
    """Extract the layout model dict from a component spec.

    If the ``layout`` field is absent, returns a default flex row/stretch layout.

    Args:
        spec: Parsed component spec dict.

    Returns:
        Dict with at minimum ``model``, ``direction``, ``align`` keys.
    """
    raw = spec.get("layout")
    if not raw:
        return dict(_DEFAULTS)

    return {
        "model": raw.get("type", _DEFAULTS["model"]),
        "direction": raw.get("direction", _DEFAULTS["direction"]),
        "align": raw.get("align", _DEFAULTS["align"]),
        **{k: v for k, v in raw.items() if k not in {"type", "direction", "align"}},
    }
