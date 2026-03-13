"""StructuralComparator — diffs spec YAML props vs. TSX props vs. Markdown props.

For each component found in ``specs/*.spec.yaml``, the tool:
1. Parses the ``props`` list from the YAML.
2. Extracts prop names from the corresponding TSX file via a regex on ``interface``
   or ``type`` declarations.
3. Extracts prop names from the Markdown props table (``| name | … |`` rows).
4. Returns a list of drift items:
   ``{component, prop, in_spec, in_code, in_docs}``
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from crewai.tools import BaseTool
from pydantic import BaseModel

# Matches optional prop names in TSX interface/type declarations
# Works for both multi-line and single-line interface bodies
_TSX_PROP_RE = re.compile(r"""(?:^|[{;,]\s*)([a-zA-Z][a-zA-Z0-9_]*)\??:\s""", re.MULTILINE)
# Markdown table row: | name | …
_MD_ROW_RE = re.compile(r"^\|\s*([a-zA-Z][a-zA-Z0-9_]*)\s*\|", re.MULTILINE)


def _spec_props(spec_path: Path) -> list[str]:
    try:
        data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "props" in data:
            return [p["name"] for p in data["props"] if isinstance(p, dict) and "name" in p]
    except Exception:  # noqa: BLE001
        pass
    return []


def _tsx_props(tsx_path: Path) -> list[str]:
    if not tsx_path.exists():
        return []
    try:
        source = tsx_path.read_text(encoding="utf-8", errors="replace")
        return list({m.group(1) for m in _TSX_PROP_RE.finditer(source)})
    except OSError:
        return []


def _md_props(md_path: Path) -> list[str]:
    if not md_path.exists():
        return []
    try:
        content = md_path.read_text(encoding="utf-8", errors="replace")
        rows = _MD_ROW_RE.findall(content)
        # Filter out header/separator rows
        return [r for r in rows if r.lower() not in ("name", "prop", "property", "-")]
    except OSError:
        return []


def compare_structure(output_dir: str) -> dict[str, Any]:
    """Compare spec YAML, TSX, and Markdown for every component.

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        Dict with ``drift`` key — list of drift items.
    """
    od = Path(output_dir)
    specs_dir = od / "specs"
    drift: list[dict[str, Any]] = []

    if not specs_dir.exists():
        return {"drift": drift}

    for spec_file in specs_dir.glob("*.spec.yaml"):
        component_name = spec_file.stem.replace(".spec", "").capitalize()
        # Best-effort: infer component name from YAML data
        try:
            raw = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and "name" in raw:
                component_name = raw["name"]
        except Exception:  # noqa: BLE001
            pass

        spec_names = _spec_props(spec_file)

        tsx_path = od / "src" / "components" / f"{component_name}.tsx"
        tsx_names = _tsx_props(tsx_path)

        md_path = od / "docs" / "components" / f"{component_name.lower()}.md"
        md_names = _md_props(md_path)

        all_props = set(spec_names) | set(tsx_names) | set(md_names)
        for prop in sorted(all_props):
            in_spec = prop in spec_names
            in_code = prop in tsx_names
            in_docs = prop in md_names
            if not (in_spec and in_code and in_docs):
                drift.append({
                    "component": component_name,
                    "prop": prop,
                    "in_spec": in_spec,
                    "in_code": in_code,
                    "in_docs": in_docs,
                })

    return {"drift": drift}


class _ComparatorInput(BaseModel):
    output_dir: str


class StructuralComparator(BaseTool):
    """Compare spec YAML props, TSX prop types, and Markdown prop table for drift."""

    name: str = "structural_comparator"
    description: str = (
        "For each component in specs/*.spec.yaml, compare props against the TSX "
        "interface and Markdown prop table. Returns {drift: [{component, prop, "
        "in_spec, in_code, in_docs}]}."
    )
    args_schema: type[BaseModel] = _ComparatorInput

    def _run(self, output_dir: str, **kwargs: Any) -> dict[str, Any]:
        return compare_structure(output_dir)
