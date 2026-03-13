"""DomainClassifier — keyword-based component→domain classification.

Classifies each component into exactly one domain using keyword scoring.
Components that match no domain keyword are assigned ``"__orphan__"``.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def classify(
    components: list[str],
    domains: dict[str, list[str]],
) -> dict[str, str]:
    """Classify each component into a domain using keyword scoring.

    For each component, the domain whose keyword list produces the highest
    cumulative match score wins. If no keywords match, the component is
    assigned ``"__orphan__"``.

    Scoring: for each keyword in a domain's list, if the keyword appears
    (case-insensitive) in the component name the domain score is incremented
    by 1. The domain with the highest score wins.

    Args:
        components: List of component names to classify.
        domains: Mapping of domain name → list of keyword strings.

    Returns:
        Mapping of component name → domain name (or ``"__orphan__"``).
    """
    result: dict[str, str] = {}
    for component in components:
        lower_name = component.lower()
        best_domain: str | None = None
        best_score = 0

        for domain, keywords in domains.items():
            score = sum(1 for kw in keywords if kw.lower() in lower_name)
            if score > best_score:
                best_score = score
                best_domain = domain

        result[component] = best_domain if best_domain is not None else "__orphan__"

    return result


class _ClassifierInput(BaseModel):
    components: list[str]
    domains: dict[str, list[str]]


class DomainClassifier(BaseTool):
    """Classify components into domains using keyword scoring."""

    name: str = "domain_classifier"
    description: str = (
        "Classify each component into exactly one domain using keyword scoring. "
        "Returns a mapping of component name to domain (or '__orphan__' if unmatched)."
    )
    args_schema: type[BaseModel] = _ClassifierInput

    def _run(
        self,
        components: list[str],
        domains: dict[str, list[str]],
        **kwargs: Any,
    ) -> dict[str, str]:
        return classify(components, domains)
