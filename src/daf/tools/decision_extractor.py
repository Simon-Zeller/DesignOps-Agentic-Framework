"""Tool: decision_extractor — normalizes decision records from a generation summary."""
from __future__ import annotations

from typing import Any


def extract_decisions(generation_summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract and normalize the decisions list from a generation summary dict.

    Args:
        generation_summary: The parsed ``generation-summary.json`` dict.

    Returns:
        A list of normalized decision dicts, each guaranteed to have
        ``title``, ``context``, ``decision``, and ``consequences`` keys.
        Returns an empty list if no decisions are found.
    """
    raw = generation_summary.get("decisions", []) or []
    normalized: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        normalized.append(
            {
                "title": entry.get("title", ""),
                "context": entry.get("context", ""),
                "decision": entry.get("decision", ""),
                "consequences": entry.get("consequences", ""),
            }
        )
    return normalized
