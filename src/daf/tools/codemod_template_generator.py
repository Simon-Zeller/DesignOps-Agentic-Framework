"""Agent 38 – CodemodTemplateGenerator tool (Release Crew, Phase 6).

Given a migration target dict {"element": "button", "ds_component": "Button"},
returns a Markdown string with "before" and "after" code blocks.
"""
from __future__ import annotations

import json
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


class CodemodTemplateGenerator(BaseTool):
    """Generate an adoption codemod example as a Markdown before/after snippet."""

    name: str = Field(default="codemod_template_generator")
    description: str = Field(
        default=(
            'Given a JSON string with "element" and "ds_component" keys, returns a '
            "Markdown string with before and after code blocks showing how to migrate "
            "from the raw HTML element to the design system component."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, target_json: str = "", **kwargs: Any) -> str:
        try:
            data: dict[str, Any] = json.loads(target_json)
            element = data.get("element", "element")
            ds_component = data.get("ds_component", "Component")
        except (json.JSONDecodeError, TypeError):
            element = "element"
            ds_component = "Component"

        before_snippet = f"<{element}>content</{element}>"
        after_snippet = f"<{ds_component}>content</{ds_component}>"

        return (
            f"# Codemod: `<{element}>` → `<{ds_component}>`\n\n"
            f"Migrate raw `<{element}>` usages to the design system `<{ds_component}>` component.\n\n"
            f"## Before\n\n"
            f"```tsx\n{before_snippet}\n```\n\n"
            f"## After\n\n"
            f"```tsx\n{after_snippet}\n```\n\n"
            f"## Notes\n\n"
            f"Replace all occurrences of `<{element}` with the `{ds_component}` import from your "
            f"design system package. Ensure you pass the equivalent props.\n"
        )
