"""Agent 44 – Validation Rule Agent (AI Semantic Layer Crew, Phase 5).

Compiles all compliance rules from token, composition, a11y, and naming
checks into ``registry/compliance-rules.json``.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.rule_compiler import RuleCompiler


def create_validation_rule_agent(model: str, output_dir: str) -> Agent:
    """Create the Validation Rule Agent (Agent 44) for the AI Semantic Layer Crew.

    Args:
        model: LLM model name (Haiku tier recommended).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Compliance rule exporter and validation rule aggregator",
        goal=(
            "Aggregate all token, composition, a11y, and naming rules from the "
            "registry files into a single, linter-consumable "
            "registry/compliance-rules.json. Enrich each rule with a clear "
            "natural-language description of *why* the rule exists."
        ),
        backstory=(
            "You are a design system compliance expert who turns quality rules into "
            "machine-readable formats. You understand that every constraint in a "
            "design system exists for a reason — accessibility, brand consistency, "
            "or technical correctness — and you communicate that reason clearly."
        ),
        tools=[RuleCompiler()],
        llm=model,
        verbose=False,
    )
