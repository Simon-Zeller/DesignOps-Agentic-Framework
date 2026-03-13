"""Agent 38 – Codemod Agent (Release Crew, Phase 6).

Factory: create_codemod_agent(model, output_dir) → crewai.Agent
Role: Adoption helper generator
Model tier: Haiku
"""
from __future__ import annotations

from crewai import Agent

from daf.tools.ast_pattern_matcher import ASTPatternMatcher
from daf.tools.codemod_template_generator import CodemodTemplateGenerator
from daf.tools.example_suite_builder import ExampleSuiteBuilder


def create_codemod_agent(model: str, output_dir: str) -> Agent:
    """Agent 38 – Adoption Helper Generator (Release Crew, Phase 6)."""
    return Agent(
        role="Adoption helper generator",
        goal=(
            "Scan generated TSX source for migration patterns using ASTPatternMatcher, "
            "generate before/after adoption codemod examples using CodemodTemplateGenerator, "
            "and write the full suite to docs/codemods/ using ExampleSuiteBuilder."
        ),
        backstory=(
            "You are a design system adoption specialist. You bridge the gap between "
            "ad-hoc UI code and structured design system components by generating clear, "
            "readable codemod examples. Your output helps developers migrate their "
            "codebases to the new design system quickly and confidently."
        ),
        tools=[
            ASTPatternMatcher(output_dir=output_dir),
            CodemodTemplateGenerator(output_dir=output_dir),
            ExampleSuiteBuilder(output_dir=output_dir),
        ],
        llm=model,
        verbose=False,
    )
