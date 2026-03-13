"""OrphanScanner — CrewAI BaseTool.

Identifies tokens that are defined but never referenced by any other token in
the adjacency-list graph. Returns a list of orphaned token paths.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


class _ScannerInput(BaseModel):
    graph: dict[str, list[str]]


class OrphanScanner(BaseTool):
    """Identify tokens that are defined but never referenced by any other token."""

    name: str = "orphan_scanner"
    description: str = (
        "Scan a reference graph for orphaned tokens — defined but never referenced. "
        "Returns list of orphaned dot-path token keys."
    )
    args_schema: type[BaseModel] = _ScannerInput

    def _run(self, graph: dict[str, list[str]], **kwargs: Any) -> list[str]:
        all_nodes = set(graph.keys())
        referenced: set[str] = set()
        for targets in graph.values():
            referenced.update(targets)
        orphans = sorted(all_nodes - referenced)
        return orphans
