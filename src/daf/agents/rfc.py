"""RFC Agent (Agent 29, Governance Crew).

Generates RFC templates and process definitions that govern when RFCs are
required and what approval criteria apply.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.rfc_template_generator import RFCTemplateGenerator
from daf.tools.process_definition_builder import ProcessDefinitionBuilder


def create_rfc_agent(model: str, output_dir: str) -> Agent:
    """Create the RFC Agent (Agent 29) for the Governance Crew.

    Args:
        model: LLM model name (should be a Haiku-tier model).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="RFC Process and Template Specialist",
        goal=(
            "Generate RFC templates and define the RFC process — determining when "
            "RFCs are required and what criteria must be met for approval."
        ),
        backstory=(
            "You are a design system governance expert who formalises decision-making "
            "processes. You create RFC templates and define clear criteria for when "
            "formal proposals are needed for design system changes."
        ),
        tools=[RFCTemplateGenerator(), ProcessDefinitionBuilder()],
        llm=model,
        verbose=False,
    )
