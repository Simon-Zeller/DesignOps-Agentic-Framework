"""Ownership Agent (Agent 26, Governance Crew).

Classifies each component and token category into a logical domain, detects
orphaned components, and writes governance/ownership.json.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.domain_classifier import DomainClassifier
from daf.tools.relationship_analyzer import RelationshipAnalyzer
from daf.tools.orphan_scanner import OrphanScanner


def create_ownership_agent(model: str, output_dir: str) -> Agent:
    """Create the Ownership Agent (Agent 26) for the Governance Crew.

    Args:
        model: LLM model name (should be a Sonnet-tier model).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Ownership and Domain Classification Specialist",
        goal=(
            "Classify every component and token category into exactly one domain, "
            "detect orphaned components, and produce a complete ownership map for the "
            "design system. Resolve multi-domain ambiguities with contextual judgment."
        ),
        backstory=(
            "You are a design system governance expert with deep knowledge of how "
            "UI components relate to product domains. You ensure every component has "
            "a clear owner and no component falls through the cracks."
        ),
        tools=[DomainClassifier(), RelationshipAnalyzer(), OrphanScanner()],
        llm=model,
        verbose=False,
    )
