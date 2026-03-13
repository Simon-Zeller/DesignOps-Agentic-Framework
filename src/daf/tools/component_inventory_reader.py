"""Agent 37 – ComponentInventoryReader tool (Release Crew, Phase 6).

Reads specs/*.spec.yaml to build a component list with name, status, and
quality score. Skips malformed YAML gracefully. Returns {"components": []}
when the specs directory is absent.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field

try:
    import yaml  # PyYAML is available in the project's environment
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


class ComponentInventoryReader(BaseTool):
    """Read component inventory from specs/*.spec.yaml."""

    name: str = Field(default="component_inventory_reader")
    description: str = Field(
        default=(
            "Reads specs/*.spec.yaml from the output directory and builds a component "
            "list with name, status, and quality score. Skips malformed YAML. "
            "Returns {\"components\": []} when specs/ is absent."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, _input: str = "", **kwargs: Any) -> dict[str, Any]:
        specs_dir = Path(self.output_dir) / "specs"
        if not specs_dir.exists():
            return {"components": []}

        components: list[dict[str, Any]] = []
        for spec_file in sorted(specs_dir.glob("*.spec.yaml")):
            try:
                if _YAML_AVAILABLE:
                    data = yaml.safe_load(spec_file.read_text(encoding="utf-8")) or {}
                else:
                    # minimal fallback: parse name: value lines
                    data = _parse_simple_yaml(spec_file.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    continue
                name = data.get("name", spec_file.stem.replace(".spec", "").title())
                status = data.get("status", "unknown")
                quality_score = data.get("quality_score", None)
                components.append({"name": name, "status": status, "quality_score": quality_score})
            except Exception:  # noqa: BLE001
                # Skip malformed files
                continue

        return {"components": components}


def _parse_simple_yaml(text: str) -> dict[str, str]:
    """Minimal key: value YAML parser (no nested structures)."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result
