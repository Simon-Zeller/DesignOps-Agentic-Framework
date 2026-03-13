"""StabilityClassifier — rule-based per-component stability status.

Classifies each component as ``"stable"``, ``"beta"``, or ``"experimental"``
based on composite score, test coverage, and explicit override tags.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

_STABLE_SCORE_THRESHOLD = 80.0
_BETA_SCORE_THRESHOLD = 70.0
_STABLE_COVERAGE_THRESHOLD = 0.80


def classify(
    components: list[str],
    scorecard: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, str]:
    """Classify each component's stability status.

    Rules (in precedence order):
    1. If ``config["explicit_tags"][component]`` is set, use it.
    2. If composite score < 70 → ``"experimental"``
    3. If composite score ≥ 80 AND coverage ≥ 0.80 → ``"stable"``
    4. Otherwise → ``"beta"``

    Args:
        components: Component names to classify.
        scorecard: Mapping of component name → ``{"composite": float, "coverage": float}``.
        config: Optional config dict; may contain ``"explicit_tags"`` mapping.

    Returns:
        Mapping of component name → stability status.
    """
    explicit_tags: dict[str, str] = config.get("explicit_tags", {})
    result: dict[str, str] = {}

    for name in components:
        if name in explicit_tags:
            result[name] = explicit_tags[name]
            continue

        data = scorecard.get(name, {})
        composite = float(data.get("composite", 0.0))
        coverage = float(data.get("coverage", 0.0))

        if composite < _BETA_SCORE_THRESHOLD:
            result[name] = "experimental"
        elif composite >= _STABLE_SCORE_THRESHOLD and coverage >= _STABLE_COVERAGE_THRESHOLD:
            result[name] = "stable"
        else:
            result[name] = "beta"

    return result


class _ClassifierInput(BaseModel):
    components: list[str]
    scorecard: dict[str, Any]
    config: dict[str, Any]


class StabilityClassifier(BaseTool):
    """Classify per-component stability status using score, coverage, and explicit tags."""

    name: str = "stability_classifier"
    description: str = (
        "Classifies each component as stable, beta, or experimental based on composite "
        "score, test coverage, and explicit override tags."
    )
    args_schema: type[BaseModel] = _ClassifierInput

    def _run(
        self,
        components: list[str],
        scorecard: dict[str, Any],
        config: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, str]:
        return classify(components, scorecard, config)
