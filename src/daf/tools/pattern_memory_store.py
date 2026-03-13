"""Pattern Memory Store — persists and retrieves generation patterns within a pipeline run."""
from __future__ import annotations

from typing import Any


class PatternMemoryStore:
    """In-process store for component generation patterns.

    Uses instance-level state to avoid inter-test contamination.
    """

    def __init__(self) -> None:
        self._patterns: dict[str, dict[str, Any]] = {}

    def store_pattern(self, component_name: str, pattern: dict[str, Any]) -> None:
        """Store a generation pattern for *component_name*.

        Args:
            component_name: PascalCase component name.
            pattern: Arbitrary dict describing prop shapes, token mappings, etc.
        """
        self._patterns[component_name] = pattern

    def retrieve_similar_patterns(self, query: str) -> list[dict[str, Any]]:
        """Retrieve patterns for components whose name is a prefix of or shares a prefix with *query*.

        Similarity is name-prefix based: ``Card`` matches ``CardHeader``,
        ``CardBody``, etc.

        Args:
            query: Component name to find similar patterns for.

        Returns:
            List of dicts with ``name`` and ``pattern`` keys, or ``[]`` if none found.
        """
        results: list[dict[str, Any]] = []
        for name, pattern in self._patterns.items():
            if query.startswith(name) or name.startswith(query):
                results.append({"name": name, "pattern": pattern})
        return results
