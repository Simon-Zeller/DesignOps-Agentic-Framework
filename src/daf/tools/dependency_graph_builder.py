"""Dependency Graph Builder — resolves inter-component dependencies and topological sorts."""
from __future__ import annotations

from collections import defaultdict, deque


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected in the component graph."""


def build_dependency_graph(specs: dict[str, dict]) -> dict[str, list[str]]:
    """Build an adjacency list (component → dependencies) from spec dicts.

    Reads the ``composedOf`` and ``allowedChildren`` fields from each spec.

    Args:
        specs: Mapping of component name → spec dict.

    Returns:
        Adjacency list mapping each component to its direct dependencies.

    Raises:
        CircularDependencyError: if a circular dependency is detected.
    """
    graph: dict[str, list[str]] = {name: [] for name in specs}

    for name, spec in specs.items():
        deps: list[str] = []
        deps.extend(spec.get("composedOf") or [])
        deps.extend(spec.get("allowedChildren") or [])
        # Only track deps that are in the known spec set
        graph[name] = [d for d in deps if d in specs]

    return graph


def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    """Return a topological ordering of the graph (Kahn's algorithm).

    Args:
        graph: Adjacency list from :func:`build_dependency_graph`.

    Returns:
        List of component names in dependency order (dependencies first).

    Raises:
        CircularDependencyError: if a cycle exists.
    """
    in_degree: dict[str, int] = defaultdict(int)
    for node in graph:
        in_degree.setdefault(node, 0)
    for node, deps in graph.items():
        for dep in deps:
            in_degree[node] += 1  # node depends on dep, so dep must come first

    # We want dependencies before dependents, so use reverse edges:
    # Build reverse graph: dep → [nodes that depend on dep]
    reverse: dict[str, list[str]] = defaultdict(list)
    for node, deps in graph.items():
        for dep in deps:
            reverse[dep].append(node)

    # Recompute in_degree as number of deps (how many things must come before)
    in_deg: dict[str, int] = {node: len(deps) for node, deps in graph.items()}

    queue: deque[str] = deque(node for node, deg in in_deg.items() if deg == 0)
    result: list[str] = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for dependent in reverse[node]:
            in_deg[dependent] -= 1
            if in_deg[dependent] == 0:
                queue.append(dependent)

    if len(result) != len(graph):
        cycle_nodes = [n for n in graph if n not in result]
        raise CircularDependencyError(
            f"Circular dependency detected among components: {', '.join(cycle_nodes)}"
        )

    return result
