"""DriftReporter — classifies drift items as auto-fixable or re-run-required.

A drift item is:
- ``auto-fixable`` when the prop is in spec AND code but missing from docs
  (docs can be patched deterministically).
- ``re-run-required`` when the prop is in spec but missing from code
  (requires a Design-to-Code re-run).
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def classify_drift(drift_items: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify each drift item.

    Args:
        drift_items: List from :func:`~daf.tools.structural_comparator.compare_structure`.

    Returns:
        Dict with ``fixable`` and ``non_fixable`` lists, each entry enriched with
        ``category`` (``auto-fixable`` | ``re-run-required`` | ``review``).
    """
    fixable: list[dict[str, Any]] = []
    non_fixable: list[dict[str, Any]] = []

    for item in drift_items:
        in_spec = item.get("in_spec", False)
        in_code = item.get("in_code", False)
        in_docs = item.get("in_docs", False)

        if in_spec and in_code and not in_docs:
            entry = {**item, "category": "auto-fixable"}
            fixable.append(entry)
        elif in_spec and not in_code:
            entry = {**item, "category": "re-run-required"}
            non_fixable.append(entry)
        else:
            entry = {**item, "category": "review"}
            non_fixable.append(entry)

    return {"fixable": fixable, "non_fixable": non_fixable}


class _ReporterInput(BaseModel):
    drift_items: list[dict[str, Any]]


class DriftReporter(BaseTool):
    """Classify drift items as auto-fixable or re-run-required."""

    name: str = "drift_reporter"
    description: str = (
        "Given a list of drift items (from StructuralComparator), classify each as "
        "auto-fixable (docs missing a prop in spec+code) or re-run-required (code "
        "missing a spec prop). Returns {fixable, non_fixable}."
    )
    args_schema: type[BaseModel] = _ReporterInput

    def _run(self, drift_items: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        return classify_drift(drift_items)
