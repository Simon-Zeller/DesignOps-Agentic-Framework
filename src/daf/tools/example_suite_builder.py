"""Agent 38 – ExampleSuiteBuilder tool (Release Crew, Phase 6).

Writes codemod Markdown files to docs/codemods/. Writes docs/codemods/README.md
stating no migrations needed when the targets list is empty.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "-", text.lower()).strip("-")


class ExampleSuiteBuilder(BaseTool):
    """Write codemod example files to docs/codemods/."""

    name: str = Field(default="example_suite_builder")
    description: str = Field(
        default=(
            "Accepts a JSON array of codemod dicts (each with 'element', 'ds_component', "
            "and optionally 'content'). Writes individual .md files to docs/codemods/. "
            "Writes docs/codemods/README.md when the list is empty."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, codemods_json: str = "", **kwargs: Any) -> str:
        codemods_dir = Path(self.output_dir) / "docs" / "codemods"
        codemods_dir.mkdir(parents=True, exist_ok=True)

        try:
            codemods: list[dict[str, Any]] = json.loads(codemods_json)
            if not isinstance(codemods, list):
                codemods = []
        except (json.JSONDecodeError, TypeError):
            codemods = []

        if not codemods:
            readme = codemods_dir / "README.md"
            readme.write_text(
                "# Adoption Codemods\n\nNo migration targets found — no codemods needed.\n",
                encoding="utf-8",
            )
            return str(readme)

        written: list[str] = []
        for idx, codemod in enumerate(codemods):
            element = codemod.get("element", f"component-{idx}")
            ds_component = codemod.get("ds_component", element.title())
            content = codemod.get("content") or (
                f"# Codemod: `<{element}>` → `<{ds_component}>`\n\n"
                f"Migrate `<{element}>` to `<{ds_component}>`.\n"
            )
            filename = _slugify(f"{element}-to-{ds_component}") + ".md"
            file_path = codemods_dir / filename
            file_path.write_text(content, encoding="utf-8")
            written.append(str(file_path))

        return json.dumps({"written": written})
