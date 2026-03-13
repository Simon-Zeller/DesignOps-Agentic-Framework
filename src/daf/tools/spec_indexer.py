"""Agent 41 – SpecIndexer tool (AI Semantic Layer Crew, Phase 5).

Reads all ``specs/*.spec.yaml`` files and returns a structured list of
component metadata (name, props, variants, states, slots).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

try:
    import yaml  # type: ignore[import-untyped]
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def _load_spec_file(path: Path) -> dict[str, Any]:
    """Load a spec YAML file, returning an empty dict on failure."""
    try:
        text = path.read_text(encoding="utf-8")
        if _YAML_AVAILABLE:
            return yaml.safe_load(text) or {}
        # Minimal YAML-like parsing fallback (key: value on separate lines)
        result: dict[str, Any] = {}
        for line in text.splitlines():
            if ":" in line and not line.strip().startswith("-"):
                key, _, val = line.partition(":")
                result[key.strip()] = val.strip()
        return result
    except OSError:
        return {}


def index_specs(output_dir: str) -> list[dict[str, Any]]:
    """Parse all spec YAML files in ``<output_dir>/specs/``.

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        List of component metadata dicts, one per spec file.
    """
    od = Path(output_dir)
    specs_dir = od / "specs"
    if not specs_dir.exists():
        return []

    components: list[dict[str, Any]] = []
    for spec_file in sorted(specs_dir.glob("*.spec.yaml")):
        data = _load_spec_file(spec_file)
        if not data:
            continue
        component: dict[str, Any] = {
            "name": data.get("name", spec_file.stem.replace(".spec", "")),
            "props": data.get("props") or [],
            "variants": data.get("variants") or [],
            "states": data.get("states") or [],
            "slots": data.get("slots") or [],
            "composition": data.get("composition") or {},
        }
        components.append(component)

    return components


class _SpecIndexerInput(BaseModel):
    output_dir: str


class SpecIndexer(BaseTool):
    """Parse ``specs/*.spec.yaml`` and return structured component metadata."""

    name: str = "spec_indexer"
    description: str = (
        "Read all spec YAML files from <output_dir>/specs/ and return a list of "
        "component metadata dicts with name, props, variants, states, and slots."
    )
    args_schema: type[BaseModel] = _SpecIndexerInput

    def _run(self, output_dir: str, **kwargs: Any) -> list[dict[str, Any]]:
        return index_specs(output_dir)
