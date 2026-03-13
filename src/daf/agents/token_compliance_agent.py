"""Token Compliance Agent (Agent 32, Analytics Crew).

Performs static analysis of all generated TSX files for hardcoded colour,
spacing, and font-size values, as well as deprecated token references.
Writes ``reports/token-compliance.json``.

Delegates all scanning logic to ``compute_token_compliance`` from
``daf.tools.composition_rule_engine`` via ``TokenComplianceScannerTool`` —
no scanning is re-implemented here.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.token_compliance_scanner import TokenComplianceScannerTool
from daf.tools.token_usage_mapper import TokenUsageMapper


def create_token_compliance_agent(model: str, output_dir: str) -> Agent:
    """Create the Token Compliance Agent (Agent 32) for the Analytics Crew.

    Args:
        model: LLM model name (Haiku tier recommended).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Token Compliance and Style Governance Analyst",
        goal=(
            "Detect every hardcoded colour, spacing, or font-size value in the "
            "generated TSX codebase and report each violation with its file path, "
            "value, type, and suggested replacement token. Produce a compliance "
            "score and summary enabling the team to quantify token adoption."
        ),
        backstory=(
            "You are a design-token compliance expert who enforces that every style "
            "value in a design system references a semantic token rather than a "
            "hardcoded literal. You have deep knowledge of DTCG token conventions "
            "and can suggest the most appropriate semantic token for each violation."
        ),
        tools=[TokenComplianceScannerTool(), TokenUsageMapper()],
        llm=model,
        verbose=False,
    )
