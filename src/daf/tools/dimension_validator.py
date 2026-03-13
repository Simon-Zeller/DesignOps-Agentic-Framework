"""Dimension Validator — checks rendered component bounding boxes against minimum thresholds."""
from __future__ import annotations

from typing import Any


def validate_dimensions(
    bbox: dict[str, Any],
    *,
    min_width: int = 4,
    min_height: int = 4,
) -> dict[str, Any]:
    """Validate that a rendered bounding box meets minimum dimension thresholds.

    Args:
        bbox: Dict with ``width`` and ``height`` keys (numbers).
        min_width: Minimum acceptable width in pixels.
        min_height: Minimum acceptable height in pixels.

    Returns:
        Dict with ``passed`` (bool) and ``reason`` (str or None) keys.
    """
    width = bbox.get("width", 0)
    height = bbox.get("height", 0)

    if width <= 0 or height <= 0:
        return {"passed": False, "reason": "zero-dimension render"}

    if width < min_width:
        return {"passed": False, "reason": f"width {width} below minimum {min_width}"}

    if height < min_height:
        return {"passed": False, "reason": f"height {height} below minimum {min_height}"}

    return {"passed": True, "reason": None}
