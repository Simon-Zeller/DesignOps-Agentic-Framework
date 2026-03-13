"""Tool: prop_table_generator — renders a Markdown prop table from a props list."""
from __future__ import annotations

from typing import Any


def generate_prop_table(props: list[dict[str, Any]]) -> str:
    """Render a Markdown prop table from a list of prop dicts.

    Args:
        props: List of prop dicts with keys ``name``, ``type``, ``required``,
            ``default``, and optionally ``description``.

    Returns:
        A Markdown table string, or a note if the list is empty.
    """
    if not props:
        return "No props declared."

    header = "| Prop | Type | Required | Default | Description |"
    separator = "|------|------|----------|---------|-------------|"
    rows = [header, separator]

    for prop in props:
        name = prop.get("name", "")
        prop_type = prop.get("type", "any")
        required = prop.get("required", False)
        default = prop.get("default", None)
        description = prop.get("description", "")

        required_str = "Yes" if required else "No"
        default_str = "—" if default is None and required else str(default) if default is not None else "—"
        rows.append(f"| {name} | {prop_type} | {required_str} | {default_str} | {description} |")

    return "\n".join(rows)
