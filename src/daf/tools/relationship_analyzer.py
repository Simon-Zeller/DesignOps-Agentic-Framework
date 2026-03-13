"""RelationshipAnalyzer — cross-domain dependency analysis from component-index.json.

Reads ``docs/component-index.json`` (produced by the Documentation Crew) and
returns a list of cross-domain dependency records. Falls back to an empty list
if the index file is absent.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def analyze(
    index_path: str,
    domain_map: dict[str, str],
) -> list[dict[str, Any]]:
    """Return cross-domain dependency records from a component index file.

    Args:
        index_path: Absolute path to ``component-index.json``.
        domain_map: Mapping of component name → domain name.

    Returns:
        List of ``{"component", "depends_on", "component_domain",
        "dependency_domain"}`` dicts for cross-domain dependencies only.
    """
    path = Path(index_path)
    if not path.exists():
        logger.warning("component-index.json not found at %s; returning empty list", index_path)
        return []

    index: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    cross_domain: list[dict[str, Any]] = []

    for component, data in index.items():
        comp_domain = domain_map.get(component)
        for dep in data.get("dependencies", []):
            dep_domain = domain_map.get(dep)
            if comp_domain and dep_domain and comp_domain != dep_domain:
                cross_domain.append(
                    {
                        "component": component,
                        "depends_on": dep,
                        "component_domain": comp_domain,
                        "dependency_domain": dep_domain,
                    }
                )

    return cross_domain


class _AnalyzerInput(BaseModel):
    index_path: str
    domain_map: dict[str, str]


class RelationshipAnalyzer(BaseTool):
    """Analyze cross-domain relationships from a component index."""

    name: str = "relationship_analyzer"
    description: str = (
        "Reads docs/component-index.json and returns cross-domain dependency records. "
        "Falls back to empty list if the file is absent."
    )
    args_schema: type[BaseModel] = _AnalyzerInput

    def _run(
        self,
        index_path: str,
        domain_map: dict[str, str],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return analyze(index_path, domain_map)
