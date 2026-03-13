"""Agent 41 – RegistryBuilder tool (AI Semantic Layer Crew, Phase 5).

Assembles and writes ``registry/components.json`` from spec metadata.
Creates the ``registry/`` directory if it does not exist.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from daf.tools.spec_indexer import index_specs
from daf.tools.primitive_registry import get_all_primitives


def build_registry(output_dir: str) -> list[dict[str, Any]]:
    """Build and write the component registry from spec YAML files.

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        List of component registry entries written to ``registry/components.json``.
    """
    od = Path(output_dir)
    registry_dir = od / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)

    components = index_specs(output_dir)
    primitives = get_all_primitives()

    entries: list[dict[str, Any]] = []
    for comp in components:
        entry: dict[str, Any] = {
            "name": comp["name"],
            "is_primitive": comp["name"] in primitives,
            "props": comp.get("props") or [],
            "variants": comp.get("variants") or [],
            "states": comp.get("states") or [],
            "slots": comp.get("slots") or [],
        }
        entries.append(entry)

    outfile = registry_dir / "components.json"
    outfile.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return entries


class _RegistryBuilderInput(BaseModel):
    output_dir: str


class RegistryBuilder(BaseTool):
    """Assemble and write ``registry/components.json`` (Agent 41, AI Semantic Layer Crew, Phase 5)."""

    name: str = "registry_builder"
    description: str = (
        "Read all spec YAML files and write registry/components.json with full "
        "component metadata. Creates registry/ directory if absent."
    )
    args_schema: type[BaseModel] = _RegistryBuilderInput

    def _run(self, output_dir: str, **kwargs: Any) -> list[dict[str, Any]]:
        return build_registry(output_dir)
