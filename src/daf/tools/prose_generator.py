"""Tool: prose_generator — builds an LLM prompt for the generation narrative."""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class ProseGenerator(BaseTool):
    """BaseTool wrapper for building prose generation prompts."""

    name: str = Field(default="prose_generator")
    description: str = Field(
        default=(
            "Accepts a JSON string with brand_analysis and decisions keys. "
            "Returns a narrative prompt string suitable for LLM prose generation."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, prompt_json: str = "", **kwargs: Any) -> str:
        import json  # noqa: PLC0415
        try:
            data = json.loads(prompt_json)
            brand_analysis = data.get("brand_analysis", {})
            decisions = data.get("decisions", [])
        except (json.JSONDecodeError, TypeError):
            brand_analysis = {}
            decisions = []
        return build_narrative_prompt(brand_analysis, decisions)


def build_narrative_prompt(brand_analysis: dict[str, Any], decisions: list[dict[str, Any]]) -> str:
    """Compose a narrative generation prompt from brand data and decision records.

    Args:
        brand_analysis: Output of ``analyze_brand_profile`` — contains
            ``archetype``, ``a11y_level``, ``modular_scale``.
        decisions: List of decision dicts, each with ``title`` and ``decision``.

    Returns:
        A non-empty prompt string suitable for passing to an LLM.
        Never raises.
    """
    archetype = brand_analysis.get("archetype", "unspecified")
    a11y_level = brand_analysis.get("a11y_level", "AA")
    modular_scale = brand_analysis.get("modular_scale", "unspecified")

    decision_lines: list[str] = []
    for d in decisions:
        title = d.get("title", "")
        decision = d.get("decision", "")
        if title:
            decision_lines.append(f"- {title}: {decision}")

    decisions_text = "\n".join(decision_lines) if decision_lines else "No explicit decisions recorded."

    return (
        f"Write a generation narrative for a design system with the following characteristics:\n\n"
        f"Brand archetype: {archetype}\n"
        f"Accessibility level: {a11y_level}\n"
        f"Modular scale ratio: {modular_scale}\n\n"
        f"Key decisions made during generation:\n{decisions_text}\n\n"
        f"Explain why these choices were made, how they relate to the brand, "
        f"and what implications they have for the design system."
    )
