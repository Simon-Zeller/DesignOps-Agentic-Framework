"""DocPatcher — appends missing prop rows to Markdown prop tables in-place.

Given a list of auto-fixable drift items (each with ``component`` and ``prop``),
the patcher locates the relevant Markdown file under ``docs/components/`` and
appends a new table row for each missing prop.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def patch_docs(output_dir: str, fixable_items: list[dict[str, Any]]) -> dict[str, Any]:
    """Append missing prop rows to Markdown prop tables.

    Args:
        output_dir: Root pipeline output directory.
        fixable_items: Auto-fixable drift items from DriftReporter.

    Returns:
        Dict with ``patched`` list of ``{component, prop, file}`` entries.
    """
    od = Path(output_dir)
    docs_dir = od / "docs" / "components"
    patched: list[dict[str, str]] = []

    # Group by component
    by_component: dict[str, list[str]] = {}
    for item in fixable_items:
        component = item.get("component", "")
        prop = item.get("prop", "")
        if component and prop:
            by_component.setdefault(component, []).append(prop)

    for component, props in by_component.items():
        md_path = docs_dir / f"{component.lower()}.md"
        if not md_path.exists():
            continue

        content = md_path.read_text(encoding="utf-8")
        additions: list[str] = []
        for prop in props:
            # Skip if prop already appears in the file
            if prop in content:
                continue
            additions.append(f"| {prop} | — | — |")

        if additions:
            content = content.rstrip() + "\n" + "\n".join(additions) + "\n"
            md_path.write_text(content, encoding="utf-8")
            for prop in props:
                patched.append({"component": component, "prop": prop, "file": str(md_path)})

    return {"patched": patched}


class _PatcherInput(BaseModel):
    output_dir: str
    fixable_items: list[dict[str, Any]]


class DocPatcher(BaseTool):
    """Append missing prop rows to Markdown documentation tables in-place."""

    name: str = "doc_patcher"
    description: str = (
        "Given auto-fixable drift items (component + prop), append missing prop rows "
        "to docs/components/<component>.md. Returns {patched: [{component, prop, file}]}."
    )
    args_schema: type[BaseModel] = _PatcherInput

    def _run(
        self,
        output_dir: str,
        fixable_items: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        return patch_docs(output_dir, fixable_items)
