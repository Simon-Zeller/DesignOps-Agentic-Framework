"""ReferenceGraphWalker — CrewAI BaseTool.

Traverses $value reference chains across all three token tier files (base,
semantic, component) loaded into a single merged key namespace. Returns an
adjacency-list graph: {source_path: [target_path, ...]} where source and
target are dot-path token keys.
"""
from __future__ import annotations

import re
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

# DTCG reference pattern: {tier.category.name}
_REF_RE = re.compile(r"^\{([a-z0-9._-]+)\}$")


def _walk_tokens(
    data: dict[str, Any],
    path: str = "",
    tier: str = "",
) -> dict[str, dict[str, Any]]:
    """Recursively walk a token dict and return {dot-path: token_obj}."""
    result: dict[str, dict[str, Any]] = {}
    for key, value in data.items():
        if key.startswith("$"):
            continue
        node_path = f"{path}.{key}" if path else key
        if isinstance(value, dict):
            if "$value" in value:
                result[node_path] = {**value, "__tier__": tier}
            else:
                result.update(_walk_tokens(value, node_path, tier))
    return result


class _WalkerInput(BaseModel):
    base: dict[str, Any]
    semantic: dict[str, Any]
    component: dict[str, Any]


class ReferenceGraphWalker(BaseTool):
    """Build a cross-tier reference adjacency-list graph from three DTCG tier dicts."""

    name: str = "reference_graph_walker"
    description: str = (
        "Build an adjacency-list reference graph from three DTCG tier files. "
        "Returns {source_path: [target_path]} where targets are resolved across all tiers."
    )
    args_schema: type[BaseModel] = _WalkerInput

    def _run(
        self,
        base: dict[str, Any],
        semantic: dict[str, Any],
        component: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, list[str]]:  # type: ignore[override]
        # Merge all tiers into a single namespace; component > semantic > base
        all_tokens: dict[str, dict[str, Any]] = {}
        all_tokens.update(_walk_tokens(base, tier="base"))
        all_tokens.update(_walk_tokens(semantic, tier="semantic"))
        all_tokens.update(_walk_tokens(component, tier="component"))

        graph: dict[str, list[str]] = {}
        for token_path, token_obj in all_tokens.items():
            graph.setdefault(token_path, [])
            raw_value = str(token_obj.get("$value", ""))
            match = _REF_RE.match(raw_value)
            if match:
                target = match.group(1)
                graph[token_path].append(target)

        return graph
