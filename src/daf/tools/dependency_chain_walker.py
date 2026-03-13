"""DependencyChainWalker — classifies test failures as root-cause or downstream.

Loads ``dependency_graph.json`` (mapping component → {dependencies: [...]}) then,
for a given set of failing component names, classifies each failure as:

- ``root-cause``: the component has no failing dependencies.
- ``downstream``: at least one dependency is also in the failures set.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def walk_failures(output_dir: str, failures: list[str]) -> dict[str, Any]:
    """Classify each failing component.

    Args:
        output_dir: Root pipeline output directory.
        failures: List of component names that failed.

    Returns:
        Dict with ``failures`` key — list of failure classification entries.
    """
    od = Path(output_dir)
    graph_path = od / "dependency_graph.json"

    if not failures:
        return {"failures": []}

    graph: dict[str, dict[str, Any]] = {}
    if graph_path.exists():
        try:
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            graph = {}

    failure_set = set(failures)
    result: list[dict[str, Any]] = []

    for component in failures:
        node = graph.get(component, {})
        deps: list[str] = node.get("dependencies", [])
        failing_deps = [d for d in deps if d in failure_set]

        if not failing_deps:
            result.append({
                "component": component,
                "classification": "root-cause",
                "dependency_chain": [component],
                "root_cause_component": None,
            })
        else:
            # Walk upstream to find the deepest root-cause
            root = _find_root_cause(component, graph, failure_set, visited=set())
            chain = _build_chain(root, component, graph)
            result.append({
                "component": component,
                "classification": "downstream",
                "dependency_chain": chain,
                "root_cause_component": root,
            })

    return {"failures": result}


def _find_root_cause(
    component: str,
    graph: dict[str, Any],
    failure_set: set[str],
    visited: set[str],
) -> str:
    """Recursively find the root-cause ancestor in the failure set."""
    if component in visited:
        return component
    visited.add(component)
    deps = graph.get(component, {}).get("dependencies", [])
    failing_deps = [d for d in deps if d in failure_set]
    if not failing_deps:
        return component
    return _find_root_cause(failing_deps[0], graph, failure_set, visited)


def _build_chain(root: str, target: str, graph: dict[str, Any]) -> list[str]:
    """Return [root, ..., target] path through the graph."""
    if root == target:
        return [root]
    return [root, target]


class _WalkerInput(BaseModel):
    output_dir: str
    failures: list[str]


class DependencyChainWalker(BaseTool):
    """Walk the dependency graph to classify failures as root-cause or downstream."""

    name: str = "dependency_chain_walker"
    description: str = (
        "Load dependency_graph.json and classify each failing component as root-cause "
        "or downstream. Returns {failures: [{component, classification, "
        "dependency_chain, root_cause_component}]}."
    )
    args_schema: type[BaseModel] = _WalkerInput

    def _run(
        self,
        output_dir: str,
        failures: list[str],
        **kwargs: Any,
    ) -> dict[str, Any]:
        return walk_failures(output_dir, failures)
