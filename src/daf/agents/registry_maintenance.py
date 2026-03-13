"""Agent 41 – Registry Maintenance Agent (AI Semantic Layer Crew, Phase 5).

Builds ``registry/components.json`` with full prop metadata, variants,
states, slots, and usage examples from spec YAMLs.
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.example_code_generator import ExampleCodeGenerator
from daf.tools.registry_builder import RegistryBuilder
from daf.tools.spec_indexer import SpecIndexer


def create_registry_maintenance_agent(model: str, output_dir: str) -> Agent:
    """Create the Registry Maintenance Agent (Agent 41) for the AI Semantic Layer Crew.

    Args:
        model: LLM model name (Haiku tier recommended).
        output_dir: Root pipeline output directory.

    Returns:
        Configured :class:`crewai.Agent` instance.
    """
    return Agent(
        role="Knowledge graph builder and registry maintenance specialist",
        goal=(
            "Parse all component spec YAML files and build a complete "
            "registry/components.json that captures every prop, variant, state, "
            "slot, and usage example. Ensure the registry is accurate, complete, "
            "and written in a format that AI coding assistants can directly consume."
        ),
        backstory=(
            "You are a design-system architect specializing in building machine-readable "
            "component knowledge bases. You have deep understanding of design system "
            "specifications and can extract structured metadata from spec files to "
            "produce a registry that LLMs can use to generate on-brand code."
        ),
        tools=[SpecIndexer(), ExampleCodeGenerator(), RegistryBuilder()],
        llm=model,
        verbose=False,
    )
