"""Agent 43 – Composition Constraint Agent (AI Semantic Layer Crew, Phase 5).

Reads composition rules and builds ``registry/composition-rules.json``
with allowed children, forbidden nesting, and example valid/invalid trees.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.composition_rule_extractor import CompositionRuleExtractor
from daf.tools.tree_validator import TreeValidator


def create_composition_constraint_agent(model: str, output_dir: str) -> Agent:
    """Create the Composition Constraint Agent (Agent 43) for the AI Semantic Layer Crew.

    Args:
        model: LLM model name (Sonnet tier recommended).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Composition constraint analyst and valid tree definer",
        goal=(
            "Extract all composition rules from the audit report or spec YAML files. "
            "Validate example component trees to confirm rules are correct. "
            "Produce registry/composition-rules.json with allowed children, "
            "forbidden nesting, required slots, and example valid/invalid trees "
            "that AI tools can use to avoid generating invalid component nesting."
        ),
        backstory=(
            "You are a component architecture expert who deeply understands which "
            "component combinations are valid versus pathological in a design system. "
            "You can reason about component tree structure and produce precise "
            "composition constraints that prevent AI tools from generating broken layouts."
        ),
        tools=[CompositionRuleExtractor(), TreeValidator()],
        llm=model,
        verbose=False,
    )
