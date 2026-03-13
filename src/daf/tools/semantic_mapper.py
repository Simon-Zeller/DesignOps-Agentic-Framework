"""Agent 42 – SemanticMapper tool (AI Semantic Layer Crew, Phase 5).

Assigns tier labels (primitive / semantic / component) to tokens, groups
them by category, and returns an enriched token list.
"""
from __future__ import annotations

import re
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

# Detects DTCG reference syntax: {some.token.path}
_REF_RE = re.compile(r"^\{.+\}$")

# Keywords that suggest component-level tokens
_COMPONENT_KEYWORDS = frozenset({
    "button", "input", "card", "badge", "alert", "modal", "nav",
    "header", "footer", "sidebar", "tooltip", "dropdown",
})


def _assign_tier(token: dict[str, Any]) -> str:
    """Assign a tier label to a token based on its name and value."""
    name_lower = token.get("name", "").lower()
    value = token.get("value", "")

    # Component tier: name contains a known component keyword
    for kw in _COMPONENT_KEYWORDS:
        if kw in name_lower:
            return "component"

    # Semantic tier: value is a reference to another token
    if isinstance(value, str) and _REF_RE.match(value):
        return "semantic"

    return "primitive"


def _category_from_type(token_type: str) -> str:
    """Map a DTCG token type to a category name."""
    mapping = {
        "color": "color",
        "fontSizes": "typography",
        "fontWeights": "typography",
        "fontFamilies": "typography",
        "lineHeights": "typography",
        "letterSpacings": "typography",
        "spacing": "spacing",
        "borderRadius": "shape",
        "borderWidth": "shape",
        "boxShadow": "elevation",
        "opacity": "opacity",
        "duration": "motion",
        "cubicBezier": "motion",
    }
    return mapping.get(token_type, "other")


def map_semantic_tokens(
    tokens: list[dict[str, Any]],
    output_dir: str = "",
) -> list[dict[str, Any]]:
    """Enrich a token list with tier labels and category groupings.

    Args:
        tokens: Flat token list from :func:`traverse_token_graph`.
        output_dir: Root pipeline output directory (unused but kept for API consistency).

    Returns:
        Enriched token list — each entry gains ``tier`` and ``category`` keys.
    """
    enriched: list[dict[str, Any]] = []
    for token in tokens:
        entry = dict(token)
        entry["tier"] = _assign_tier(token)
        entry["category"] = _category_from_type(token.get("type", "unknown"))
        enriched.append(entry)
    return enriched


class _SemanticMapperInput(BaseModel):
    tokens: list[dict[str, Any]]
    output_dir: str = ""


class SemanticMapper(BaseTool):
    """Assign tier labels and category groupings to tokens (Agent 42, AI Semantic Layer Crew, Phase 5)."""

    name: str = "semantic_mapper"
    description: str = (
        "Enrich a flat token list with 'tier' (primitive/semantic/component) and "
        "'category' groupings. Returns the enriched token list."
    )
    args_schema: type[BaseModel] = _SemanticMapperInput

    def _run(
        self, tokens: list[dict[str, Any]], output_dir: str = "", **kwargs: Any
    ) -> list[dict[str, Any]]:
        return map_semantic_tokens(tokens, output_dir)
