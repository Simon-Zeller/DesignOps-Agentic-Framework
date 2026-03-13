"""CircularRefDetector — CrewAI BaseTool.

Detects cycles in a reference graph using iterative DFS. Takes an
adjacency-list graph {node: [neighbour, ...]} and returns a list of cycles,
where each cycle is a list of node names forming the cycle path.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


class _DetectorInput(BaseModel):
    graph: dict[str, list[str]]


def _detect_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """DFS-based cycle detection on a directed graph.

    Returns a list of cycles; each cycle is the list of nodes in the cycle path
    (first node repeated at end for clarity).
    """
    visited: set[str] = set()
    rec_stack: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str, path: list[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbour in graph.get(node, []):
            if neighbour not in visited:
                dfs(neighbour, path)
            elif neighbour in rec_stack:
                # Found a cycle — extract it
                cycle_start = path.index(neighbour)
                cycle = path[cycle_start:] + [neighbour]
                cycles.append(cycle)

        path.pop()
        rec_stack.discard(node)

    for node in list(graph.keys()):
        if node not in visited:
            dfs(node, [])

    return cycles


class CircularRefDetector(BaseTool):
    """Detect circular references in a token reference graph using DFS."""

    name: str = "circular_ref_detector"
    description: str = (
        "Detect cycles in an adjacency-list reference graph. "
        "Returns a list of cycle paths (empty list if graph is a valid DAG)."
    )
    args_schema: type[BaseModel] = _DetectorInput

    def _run(self, graph: dict[str, list[str]], **kwargs: Any) -> list[list[str]]:
        return _detect_cycles(graph)
