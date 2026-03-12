"""ConsistencyChecker — detects semantic contradictions in a brand profile."""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool

# Severity constants
ERROR = "error"
WARNING = "warning"


def _get(profile: dict[str, Any], *path: str) -> Any:
    """Safely navigate a nested dict; returns None if any key is missing."""
    node: Any = profile
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


# ── Rule definitions ──────────────────────────────────────────────────────────
#
# Each rule is a tuple:
#   (predicate(profile) -> bool, field_path: str, message: str, severity: str)
#
# Rules are evaluated in order; all matching rules produce findings.

def _rules() -> list[tuple[Any, str, str, str]]:
    return [
        # ── Error-severity rules ───────────────────────────────────────────
        (
            lambda p: (
                _get(p, "spacing", "density") == "compact"
                and isinstance(_get(p, "spacing", "baseUnit"), (int, float))
                and _get(p, "spacing", "baseUnit") > 8
            ),
            "spacing",
            (
                "Compact density with a {baseUnit}px base unit is contradictory"
                " — compact typically uses 4px."
            ),
            ERROR,
        ),
        # ── Warning-severity rules ─────────────────────────────────────────
        (
            lambda p: (
                _get(p, "archetype") == "mobile-first"
                and _get(p, "componentScope") == "comprehensive"
            ),
            "componentScope",
            (
                "Mobile-first archetype with comprehensive scope is unusual"
                " — comprehensive components may not be optimized for mobile-first density."
            ),
            WARNING,
        ),
        (
            lambda p: (
                _get(p, "archetype") == "multi-brand"
                and _get(p, "themes", "brandOverrides") is False
            ),
            "themes.brandOverrides",
            (
                "Multi-brand archetype with brandOverrides disabled is unusual"
                " — enable brandOverrides to allow per-brand theme customization."
            ),
            WARNING,
        ),
        (
            lambda p: (
                _get(p, "motion") == "expressive"
                and _get(p, "accessibility") == "AAA"
            ),
            "motion",
            (
                "Expressive motion with AAA accessibility requires a reduced motion"
                " alternative to meet WCAG 2.1 SC 2.3.3."
            ),
            WARNING,
        ),
        (
            lambda p: (
                _get(p, "archetype") == "consumer-b2c"
                and _get(p, "accessibility") == "AAA"
            ),
            "accessibility",
            (
                "AAA accessibility with the consumer-b2c archetype is unusual"
                " — consumer products typically target AA."
            ),
            WARNING,
        ),
    ]


class ConsistencyChecker(BaseTool):
    """Evaluates a flat list of consistency rules against a brand profile.

    Returns a list of ``{"field": str, "message": str, "severity": "error"|"warning"}``
    objects for every triggered rule, or an empty list for a fully consistent profile.
    """

    name: str = "consistency_checker"
    description: str = (
        "Checks a brand profile dict for semantic contradictions. "
        "Returns a list of findings with field, message, and severity. "
        "Empty list means no issues found."
    )

    def _run(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for predicate, field, message_template, severity in _rules():
            try:
                triggered = predicate(profile)
            except Exception:
                triggered = False
            if triggered:
                base_unit = _get(profile, "spacing", "baseUnit")
                message = message_template.format(baseUnit=base_unit or "?")
                findings.append(
                    {"field": field, "message": message, "severity": severity}
                )
        return findings
