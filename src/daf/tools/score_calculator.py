"""Score Calculator — computes weighted 0–100 composite quality score.

Weights:
- test_coverage:          25%
- a11y_pass_rate:         25%
- token_compliance:       20%
- composition_depth_score: 15%
- spec_completeness:      15%
"""
from __future__ import annotations

from typing import Any

_WEIGHTS: dict[str, float] = {
    "test_coverage": 0.25,
    "a11y_pass_rate": 0.25,
    "token_compliance": 0.20,
    "composition_depth_score": 0.15,
    "spec_completeness": 0.15,
}


def calculate_score(sub_scores: dict[str, float | None]) -> dict[str, Any]:
    """Compute the weighted composite quality score from *sub_scores*.

    If ``test_coverage`` is ``None`` (unavailable), it defaults to ``0.0`` and
    the ``coverage_unavailable`` flag is set.

    Args:
        sub_scores: Dict mapping sub-score name → float 0.0–1.0 (or None for coverage).

    Returns:
        ``{
            "composite": float,  # 0–100
            "sub_scores": {...},
            "coverage_unavailable": bool,  # only present when True
        }``
    """
    coverage_unavailable = False
    resolved: dict[str, float] = {}

    for key, weight in _WEIGHTS.items():  # noqa: B007
        value = sub_scores.get(key)
        if value is None:
            if key == "test_coverage":
                coverage_unavailable = True
                value = 0.0
            else:
                value = 0.0
        resolved[key] = float(value)

    composite = sum(resolved[k] * w for k, w in _WEIGHTS.items()) * 100.0

    result: dict[str, Any] = {
        "composite": round(composite, 6),
        "sub_scores": resolved,
    }
    if coverage_unavailable:
        result["coverage_unavailable"] = True

    return result
