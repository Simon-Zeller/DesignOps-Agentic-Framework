"""Threshold Gate — applies the 70/100 quality gate to component scores."""
from __future__ import annotations

from typing import Any


def apply_gate(score: float, threshold: float = 70.0) -> dict[str, Any]:
    """Apply quality gate for a single component.

    Args:
        score: Composite quality score (0–100).
        threshold: Gate threshold (default 70.0).

    Returns:
        ``{"gate": "passed" | "failed", "verdict": bool}``
    """
    passed = score >= threshold
    return {
        "gate": "passed" if passed else "failed",
        "verdict": passed,
    }


def gate_components(
    scores: list[dict[str, Any]],
    threshold: float = 70.0,
) -> dict[str, list[str]]:
    """Apply the quality gate to a list of component score dicts.

    Args:
        scores: List of ``{"name": str, "composite": float, ...}`` dicts.
        threshold: Gate threshold (default 70.0).

    Returns:
        ``{"passed": [names...], "failed": [names...]}``
    """
    passed: list[str] = []
    failed: list[str] = []

    for item in scores:
        name = item["name"]
        composite = float(item.get("composite", 0.0))
        if composite >= threshold:
            passed.append(name)
        else:
            failed.append(name)

    return {"passed": passed, "failed": failed}
