"""Agent 45 – Context Serializer Agent (AI Semantic Layer Crew, Phase 5).

Reads all four registry files, applies token-budget optimisation, and
writes ``.cursorrules``, ``copilot-instructions.md``, and ``ai-context.json``.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.context_formatter import ContextFormatter
from daf.tools.multi_format_serializer import MultiFormatSerializer
from daf.tools.token_budget_optimizer import TokenBudgetOptimizer


def create_context_serializer_agent(model: str, output_dir: str) -> Agent:
    """Create the Context Serializer Agent (Agent 45) for the AI Semantic Layer Crew.

    Args:
        model: LLM model name (Sonnet tier recommended).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="AI context packager and multi-format serialization specialist",
        goal=(
            "Read all four registry files, determine which content is highest-signal "
            "for each AI consumer format, apply token-budget optimisation to stay "
            "within IDE context window limits, and write the final "
            ".cursorrules, copilot-instructions.md, and ai-context.json files."
        ),
        backstory=(
            "You are an expert in AI context engineering — optimising information density "
            "within strict token budgets. You understand the differences between Cursor, "
            "GitHub Copilot, and generic LLM interfaces and know how to tailor context "
            "delivery for each. You always prioritise actionable information over "
            "exhaustive coverage when token budgets are tight."
        ),
        tools=[ContextFormatter(), TokenBudgetOptimizer(), MultiFormatSerializer()],
        llm=model,
        verbose=False,
    )
