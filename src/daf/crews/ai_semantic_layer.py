"""AI Semantic Layer Crew (Agents 41–45, Phase 5).

Replaces the stub with a real CrewAI Crew housing five agents — Registry
Maintenance, Token Resolution, Composition Constraint, Validation Rule, and
Context Serializer — running tasks T1–T5 in sequential order.

Pre-flight guard: raises ``RuntimeError`` if no ``*.spec.yaml`` files are
found in ``<output_dir>/specs/``, as Agent 41 requires spec input.
"""
from __future__ import annotations

from pathlib import Path

from crewai import Crew, Task

from daf.agents.composition_constraint import create_composition_constraint_agent
from daf.agents.context_serializer import create_context_serializer_agent
from daf.agents.registry_maintenance import create_registry_maintenance_agent
from daf.agents.token_resolution import create_token_resolution_agent
from daf.agents.validation_rule import create_validation_rule_agent

_SONNET_MODEL = "anthropic/claude-sonnet-4-20250514"
_HAIKU_MODEL = "anthropic/claude-sonnet-4-20250514"


def create_ai_semantic_layer_crew(output_dir: str) -> Crew:
    """Create the AI Semantic Layer Crew for *output_dir*.

    Pre-flight: verifies that ``specs/*.spec.yaml`` files exist.

    Args:
        output_dir: Root pipeline output directory.

    Raises:
        RuntimeError: If no ``specs/*.spec.yaml`` files are found.

    Returns:
        A :class:`crewai.Crew` with 5 tasks wired T1→T5.
    """
    od = Path(output_dir)
    spec_files = list((od / "specs").glob("*.spec.yaml")) if (od / "specs").exists() else []

    if not spec_files:
        raise RuntimeError(
            "AI Semantic Layer Crew pre-flight failed — no specs/*.spec.yaml files found "
            f"in {od / 'specs'}. Ensure the Token Engine Crew has completed before Phase 5."
        )

    # Ensure registry/ directory exists
    (od / "registry").mkdir(parents=True, exist_ok=True)

    # Instantiate agents
    registry_agent = create_registry_maintenance_agent(_HAIKU_MODEL, output_dir)
    token_agent = create_token_resolution_agent(_HAIKU_MODEL, output_dir)
    composition_agent = create_composition_constraint_agent(_SONNET_MODEL, output_dir)
    validation_agent = create_validation_rule_agent(_HAIKU_MODEL, output_dir)
    serializer_agent = create_context_serializer_agent(_SONNET_MODEL, output_dir)

    # Define tasks T1–T5
    t1_registry = Task(
        description=(
            f"Parse all spec YAML files in {od / 'specs'} and build a complete "
            "component registry. Index all component metadata (props, variants, "
            "states, slots) and generate JSX usage examples. "
            "Write the result to registry/components.json."
        ),
        expected_output=(
            "JSON file at registry/components.json containing an array of component "
            "registry entries, each with name, props, variants, states, slots, and "
            "usage examples."
        ),
        agent=registry_agent,
    )

    t2_tokens = Task(
        description=(
            f"Traverse all compiled DTCG token files in {od / 'tokens'}. "
            "Resolve all token reference chains to their final values. "
            "Assign semantic tier labels (primitive/semantic/component) and "
            "group tokens by category. Write the result to registry/tokens.json."
        ),
        expected_output=(
            "JSON file at registry/tokens.json containing an array of resolved token "
            "entries, each with name, value, type, tier, and category."
        ),
        agent=token_agent,
        context=[t1_registry],
    )

    t3_composition = Task(
        description=(
            f"Extract composition rules from {od / 'reports' / 'composition-audit.json'} "
            f"(falling back to spec YAML files in {od / 'specs'} if absent). "
            "Validate example component trees against the extracted rules. "
            "Write the result to registry/composition-rules.json."
        ),
        expected_output=(
            "JSON file at registry/composition-rules.json containing an array of "
            "composition rules, each with component, allowed_children, forbidden_children, "
            "and example valid/invalid trees."
        ),
        agent=composition_agent,
        context=[t2_tokens],
    )

    t4_validation = Task(
        description=(
            "Compile all compliance rules from registry/components.json, "
            "registry/tokens.json, and registry/composition-rules.json into "
            "four categories: token_rules, composition_rules, a11y_rules, naming_rules. "
            "Write the aggregated result to registry/compliance-rules.json."
        ),
        expected_output=(
            "JSON file at registry/compliance-rules.json with four top-level keys: "
            "token_rules, composition_rules, a11y_rules, naming_rules, each containing "
            "an array of rule objects."
        ),
        agent=validation_agent,
        context=[t3_composition],
    )

    t5_serialize = Task(
        description=(
            "Read registry/components.json, registry/tokens.json, "
            "registry/composition-rules.json, and registry/compliance-rules.json. "
            "Format registry data into IDE-specific context strings. "
            "Apply token-budget optimisation to ensure .cursorrules and "
            "copilot-instructions.md stay within IDE context window limits. "
            f"Write .cursorrules, copilot-instructions.md, and ai-context.json to {od}."
        ),
        expected_output=(
            f".cursorrules written to {od / '.cursorrules'} (optimised for Cursor IDE). "
            f"copilot-instructions.md written to {od / 'copilot-instructions.md'} (for GitHub Copilot). "
            f"ai-context.json written to {od / 'ai-context.json'} (unified JSON for generic LLMs)."
        ),
        agent=serializer_agent,
        context=[t4_validation],
    )

    return Crew(
        agents=[registry_agent, token_agent, composition_agent, validation_agent, serializer_agent],
        tasks=[t1_registry, t2_tokens, t3_composition, t4_validation, t5_serialize],
        verbose=False,
    )

