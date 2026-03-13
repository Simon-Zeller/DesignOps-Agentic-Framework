"""Tool: readme_template — renders a project docs/README.md from component and token lists."""
from __future__ import annotations


def render_readme(component_names: list[str], token_categories: list[str]) -> str:
    """Render a project README with install instructions and component links.

    Args:
        component_names: List of component names (PascalCase).
        token_categories: List of top-level token category names.

    Returns:
        A Markdown README string.
    """
    lines: list[str] = [
        "# Design System",
        "",
        "## Installation",
        "",
        "```bash",
        "npm install @acme/design-system",
        "```",
        "",
        "## Quick Start",
        "",
        "```tsx",
        "import { Button } from '@acme/design-system';",
        "```",
        "",
        "## Components",
        "",
    ]

    if component_names:
        for name in component_names:
            lines.append(f"- [{name}](docs/components/{name}.md)")
    else:
        lines.append("No components generated yet.")

    lines += [
        "",
        "## Tokens",
        "",
    ]

    if token_categories:
        for category in token_categories:
            lines.append(f"- {category}")
    else:
        lines.append("No token categories available.")

    lines += [
        "",
        "## Documentation",
        "",
        "Full documentation is available in the `docs/` directory.",
        "",
    ]

    return "\n".join(lines)
