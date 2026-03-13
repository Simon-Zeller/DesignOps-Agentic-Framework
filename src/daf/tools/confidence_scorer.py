"""Confidence Scorer — computes a 0–100 confidence score per generated component."""
from __future__ import annotations

from typing import Any

_WEIGHTS = {
    "spec_completeness": 0.20,
    "lint_pass": 0.20,
    "variant_coverage": 0.20,
    "render_pass": 0.20,
    "compilation_pass": 0.20,
}

_LOW_CONFIDENCE_THRESHOLD = 60
_HIGH_CONFIDENCE_THRESHOLD = 80


def compute_confidence(scores: dict[str, Any]) -> dict[str, Any] | int:
    """Compute a 0–100 confidence score from weighted sub-scores.

    When ``render_available`` is ``False``, the render sub-score weight is
    excluded and the remaining weights are scaled proportionally to sum to 1.0.

    Args:
        scores: Dict containing float sub-scores (0.0–1.0) keyed by sub-score name,
                plus a boolean ``render_available`` key.

    Returns:
        An ``int`` score (0–100) when the score is ≥ 60, or a dict with
        ``score``, ``low_confidence``, and ``high_confidence`` keys when below 60.
        A perfect score of 100 is always returned as an ``int``.
    """
    render_available = scores.get("render_available", True)

    active_weights = dict(_WEIGHTS)
    if not render_available:
        del active_weights["render_pass"]

    # Normalise weights to sum to 1.0
    total_weight = sum(active_weights.values())
    if total_weight == 0:
        return 0

    weighted_sum = 0.0
    for key, weight in active_weights.items():
        value = float(scores.get(key, 0.0))
        weighted_sum += value * (weight / total_weight)

    raw_score = int(round(weighted_sum * 100))
    score = max(0, min(100, raw_score))

    if score >= _HIGH_CONFIDENCE_THRESHOLD:
        return score  # return plain int for high-confidence results

    return {
        "score": score,
        "low_confidence": score < _LOW_CONFIDENCE_THRESHOLD,
        "high_confidence": score >= _HIGH_CONFIDENCE_THRESHOLD,
    }
