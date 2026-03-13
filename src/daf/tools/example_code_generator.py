"""Tool: example_code_generator — produces a TSX code stub for a component variant.

Also exposes :class:`ExampleCodeGenerator` (Agent 41, AI Semantic Layer Crew, Phase 5),
a :class:`crewai.tools.BaseTool` that generates JSX usage examples from spec prop defs.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def generate_example_stub(component_name: str, variant: str) -> str:
    """Generate a minimal TSX code fence stub for a component variant.

    Args:
        component_name: The PascalCase component name (e.g. ``"Button"``).
        variant: The variant name (e.g. ``"primary"``).

    Returns:
        A Markdown TSX fenced code block string.
    """
    return f"""```tsx
import {{ {component_name} }} from './components/{component_name}';

// {variant} variant
export default function Example() {{
  return <{component_name} variant="{variant}" />;
}}
```"""


def _generate_examples_for_spec(component: dict[str, Any]) -> list[str]:
    """Generate JSX examples for a component spec dict."""
    name: str = component.get("name", "Component")
    variants: list[Any] = component.get("variants") or []
    if not variants:
        return [generate_example_stub(name, "default")]
    examples: list[str] = []
    for v in variants:
        variant_name = v if isinstance(v, str) else (v.get("name", "default") if isinstance(v, dict) else "default")
        examples.append(generate_example_stub(name, variant_name))
    return examples


class _ExampleCodeGeneratorInput(BaseModel):
    component: dict[str, Any]
    output_dir: str = ""


class ExampleCodeGenerator(BaseTool):
    """Generate JSX usage examples from a component spec dict (Agent 41, AI Semantic Layer Crew, Phase 5)."""

    name: str = "example_code_generator"
    description: str = (
        "Generate JSX usage examples from a component spec dict. "
        "Accepts a component dict with 'name' and 'variants' keys. "
        "Returns a list of TSX code fence strings."
    )
    args_schema: type[BaseModel] = _ExampleCodeGeneratorInput

    def _run(self, component: dict[str, Any], output_dir: str = "", **kwargs: Any) -> list[str]:
        return _generate_examples_for_spec(component)
