"""Tool: example_code_generator — produces a TSX code stub for a component variant."""
from __future__ import annotations


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
