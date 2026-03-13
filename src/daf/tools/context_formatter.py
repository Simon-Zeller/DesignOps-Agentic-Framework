"""Agent 45 – ContextFormatter tool (AI Semantic Layer Crew, Phase 5).

Transforms the aggregated registry JSON into format strings suitable for
``.cursorrules`` (Cursor IDE) and ``copilot-instructions.md`` (GitHub Copilot).
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def _format_props(props: list[Any]) -> str:
    """Render a props list as a compact string."""
    if not props:
        return ""
    lines: list[str] = []
    for p in props:
        if isinstance(p, dict):
            name = p.get("name", "")
            ptype = p.get("type", "")
            default = p.get("default", "")
            line = f"  - {name}: {ptype}"
            if default:
                line += f" (default: {default})"
            lines.append(line)
        elif isinstance(p, str):
            lines.append(f"  - {p}")
    return "\n".join(lines)


def format_registry(
    registry: dict[str, Any],
    output_dir: str = "",
) -> dict[str, str]:
    """Format registry data into ``.cursorrules`` and ``copilot-instructions.md`` strings.

    Args:
        registry: Dict with ``components``, ``tokens``, ``composition_rules``,
            and ``compliance_rules`` keys.
        output_dir: Root pipeline output directory (unused; kept for API consistency).

    Returns:
        Dict with ``cursorrules`` and ``copilot_instructions`` string values.
    """
    components: list[dict[str, Any]] = registry.get("components") or []
    tokens: list[dict[str, Any]] = registry.get("tokens") or []
    composition_rules: list[dict[str, Any]] = registry.get("composition_rules") or []

    # --- .cursorrules format ---
    cursor_lines: list[str] = ["# Design System Rules", ""]

    if components:
        cursor_lines.append("## Components")
        for comp in components:
            name = comp.get("name", "")
            cursor_lines.append(f"### {name}")
            props_str = _format_props(comp.get("props") or [])
            if props_str:
                cursor_lines.append("**Props:**")
                cursor_lines.append(props_str)
            variants = comp.get("variants") or []
            if variants:
                cursor_lines.append(f"**Variants:** {', '.join(str(v) for v in variants)}")
            cursor_lines.append("")

    if tokens:
        cursor_lines.append("## Design Tokens")
        for token in tokens[:20]:  # limit for brevity
            name = token.get("name", "")
            value = token.get("value", "")
            cursor_lines.append(f"- `{name}`: {value}")
        cursor_lines.append("")

    if composition_rules:
        cursor_lines.append("## Composition Rules")
        for rule in composition_rules:
            comp_name = rule.get("component", "")
            allowed = rule.get("allowed_children") or []
            forbidden = rule.get("forbidden_children") or []
            if allowed:
                cursor_lines.append(f"- {comp_name}: allowed children: {', '.join(allowed)}")
            if forbidden:
                cursor_lines.append(f"- {comp_name}: forbidden children: {', '.join(forbidden)}")
        cursor_lines.append("")

    cursorrules = "\n".join(cursor_lines)

    # --- copilot-instructions.md format ---
    copilot_lines: list[str] = [
        "# GitHub Copilot Instructions",
        "",
        "This design system provides the following components and tokens.",
        "Always use the provided design tokens instead of hardcoded values.",
        "",
    ]

    if components:
        copilot_lines.append("## Available Components")
        copilot_lines.append("")
        for comp in components:
            name = comp.get("name", "")
            copilot_lines.append(f"- **{name}**")
        copilot_lines.append("")

    if tokens:
        copilot_lines.append("## Design Tokens (excerpt)")
        copilot_lines.append("")
        for token in tokens[:10]:
            name = token.get("name", "")
            value = token.get("value", "")
            copilot_lines.append(f"- `{name}`: `{value}`")
        copilot_lines.append("")

    copilot_instructions = "\n".join(copilot_lines)

    return {
        "cursorrules": cursorrules,
        "copilot_instructions": copilot_instructions,
    }


class _ContextFormatterInput(BaseModel):
    registry: dict[str, Any]
    output_dir: str = ""


class ContextFormatter(BaseTool):
    """Format registry JSON into IDE-specific context strings (Agent 45, AI Semantic Layer Crew, Phase 5)."""

    name: str = "context_formatter"
    description: str = (
        "Transform aggregated registry JSON into .cursorrules and "
        "copilot-instructions.md format strings. Accepts a registry dict with "
        "components, tokens, composition_rules, and compliance_rules."
    )
    args_schema: type[BaseModel] = _ContextFormatterInput

    def _run(
        self, registry: dict[str, Any], output_dir: str = "", **kwargs: Any
    ) -> dict[str, str]:
        return format_registry(registry, output_dir)
