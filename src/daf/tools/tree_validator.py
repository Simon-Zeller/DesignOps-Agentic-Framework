"""Agent 43 – TreeValidator tool (AI Semantic Layer Crew, Phase 5).

Validates a component tree dict against a set of composition rules and
returns a ``{valid, violations}`` result dict.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def _get_rule(component: str, rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find the rule dict for *component*, case-insensitively."""
    comp_lower = component.lower()
    for rule in rules:
        if rule.get("component", "").lower() == comp_lower:
            return rule
    return None


def validate_tree(
    tree: dict[str, Any],
    rules: list[dict[str, Any]],
    output_dir: str = "",
) -> dict[str, Any]:
    """Validate *tree* against *rules* recursively.

    Args:
        tree: Component tree dict with ``component`` and ``children`` keys.
        rules: List of composition rule dicts (from :func:`extract_composition_rules`).
        output_dir: Root pipeline output directory (unused; kept for API consistency).

    Returns:
        Dict with ``valid`` (bool) and ``violations`` (list of str) keys.
    """
    violations: list[str] = []
    _check_node(tree, rules, violations)
    return {"valid": len(violations) == 0, "violations": violations}


def _check_node(
    node: dict[str, Any],
    rules: list[dict[str, Any]],
    violations: list[str],
) -> None:
    """Recursively check a tree node for composition violations."""
    component = node.get("component", "")
    children: list[dict[str, Any]] = node.get("children") or []
    rule = _get_rule(component, rules)

    if rule:
        forbidden: list[str] = [c.lower() for c in (rule.get("forbidden_children") or [])]
        allowed_raw: list[str] = rule.get("allowed_children") or []
        allowed: list[str] = [c.lower() for c in allowed_raw]

        for child in children:
            child_name = child.get("component", "")
            child_lower = child_name.lower()

            if allowed and child_lower not in allowed:
                violations.append(
                    f"{component}: child '{child_name}' is not in allowed_children {allowed_raw}"
                )

            if child_lower in forbidden:
                violations.append(
                    f"{component}: child '{child_name}' is in forbidden_children"
                )

    for child in children:
        _check_node(child, rules, violations)


class _TreeValidatorInput(BaseModel):
    tree: dict[str, Any]
    rules: list[dict[str, Any]]
    output_dir: str = ""


class TreeValidator(BaseTool):
    """Validate a component tree against composition rules (Agent 43, AI Semantic Layer Crew, Phase 5)."""

    name: str = "tree_validator"
    description: str = (
        "Validate a component tree dict against composition rules. "
        "Returns {valid: bool, violations: list[str]}."
    )
    args_schema: type[BaseModel] = _TreeValidatorInput

    def _run(
        self,
        tree: dict[str, Any],
        rules: list[dict[str, Any]],
        output_dir: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        return validate_tree(tree, rules, output_dir)
