"""Workflow Agent (Agent 27, Governance Crew).

Generates the workflow state machine definition from quality gate thresholds
and ownership structure, writing governance/workflow.json.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.workflow_state_machine import WorkflowStateMachine
from daf.tools.gate_mapper import GateMapper


def create_workflow_agent(model: str, output_dir: str) -> Agent:
    """Create the Workflow Agent (Agent 27) for the Governance Crew.

    Args:
        model: LLM model name (should be a Haiku-tier model).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Workflow Definition Specialist",
        goal=(
            "Generate comprehensive workflow state machine definitions that encode "
            "the quality gate checkpoints for token and component change pipelines."
        ),
        backstory=(
            "You are a process engineering expert who designs governance workflows "
            "for design systems. You translate quality gate requirements into "
            "actionable state machine definitions that guide contributors."
        ),
        tools=[WorkflowStateMachine(), GateMapper()],
        llm=model,
        verbose=False,
    )
