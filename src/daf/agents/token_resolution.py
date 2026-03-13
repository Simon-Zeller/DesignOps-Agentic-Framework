"""Agent 42 – Token Resolution Agent (AI Semantic Layer Crew, Phase 5).

Traverses the compiled token graph and builds ``registry/tokens.json``
with resolved values, tier labels, and semantic descriptions.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.semantic_mapper import SemanticMapper
from daf.tools.token_graph_traverser import TokenGraphTraverser


def create_token_resolution_agent(model: str, output_dir: str) -> Agent:
    """Create the Token Resolution Agent (Agent 42) for the AI Semantic Layer Crew.

    Args:
        model: LLM model name (Haiku tier recommended).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Semantic intent mapper and token resolution specialist",
        goal=(
            "Traverse the compiled DTCG token graph, resolve all reference chains, "
            "assign semantic tier labels (primitive/semantic/component), and produce "
            "registry/tokens.json with natural-language intent descriptions that "
            "enable intent-to-token resolution for AI coding tools."
        ),
        backstory=(
            "You are a design-token expert who can map raw token values to human-readable "
            "semantic intent. You understand DTCG token hierarchies and can explain "
            "what each token is *for* — not just what its value is. You produce a "
            "token registry that allows AI assistants to find the right token from a "
            "natural-language description like 'muted background' or 'action color'."
        ),
        tools=[TokenGraphTraverser(), SemanticMapper()],
        llm=model,
        verbose=False,
    )
