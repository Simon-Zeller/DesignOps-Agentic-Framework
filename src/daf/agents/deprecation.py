"""Deprecation Agent (Agent 28, Governance Crew).

Assigns lifecycle status to components and generates the deprecation policy
configuration, writing governance/deprecation-policy.json.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.lifecycle_tagger import LifecycleTagger
from daf.tools.deprecation_policy_generator import DeprecationPolicyGenerator
from daf.tools.stability_classifier import StabilityClassifier
from daf.tools.deprecation_tagger import DeprecationTagger


def create_deprecation_agent(model: str, output_dir: str) -> Agent:
    """Create the Deprecation Agent (Agent 28) for the Governance Crew.

    Args:
        model: LLM model name (should be a Haiku-tier model).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Deprecation and Lifecycle Policy Specialist",
        goal=(
            "Classify component lifecycle status, tag deprecated tokens, and generate "
            "a comprehensive deprecation policy with grace periods and migration guidance."
        ),
        backstory=(
            "You are a design system lifecycle expert who ensures that deprecated "
            "components and tokens are handled with clear migration paths and "
            "appropriate transition periods."
        ),
        tools=[
            LifecycleTagger(),
            DeprecationPolicyGenerator(),
            StabilityClassifier(),
            DeprecationTagger(),
        ],
        llm=model,
        verbose=False,
    )
