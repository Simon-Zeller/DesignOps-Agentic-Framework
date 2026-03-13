"""Agent 45 – MultiFormatSerializer tool (AI Semantic Layer Crew, Phase 5).

Writes the three AI context output files:
- ``.cursorrules``
- ``copilot-instructions.md``
- ``ai-context.json``
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def serialize_multi_format(
    cursorrules: str,
    copilot_instructions: str,
    ai_context: dict[str, Any],
    output_dir: str,
) -> dict[str, str]:
    """Write the three AI context files to *output_dir*.

    Args:
        cursorrules: Content for ``.cursorrules``.
        copilot_instructions: Content for ``copilot-instructions.md``.
        ai_context: Dict written as JSON to ``ai-context.json``.
        output_dir: Root pipeline output directory.

    Returns:
        Dict of ``{file_path: absolute_path_written}`` for each file.
    """
    od = Path(output_dir)
    od.mkdir(parents=True, exist_ok=True)

    cursorrules_path = od / ".cursorrules"
    copilot_path = od / "copilot-instructions.md"
    ai_context_path = od / "ai-context.json"

    cursorrules_path.write_text(cursorrules, encoding="utf-8")
    copilot_path.write_text(copilot_instructions, encoding="utf-8")
    ai_context_path.write_text(json.dumps(ai_context, indent=2), encoding="utf-8")

    return {
        "cursorrules": str(cursorrules_path),
        "copilot_instructions": str(copilot_path),
        "ai_context": str(ai_context_path),
    }


class _MultiFormatSerializerInput(BaseModel):
    cursorrules: str
    copilot_instructions: str
    ai_context: dict[str, Any]
    output_dir: str


class MultiFormatSerializer(BaseTool):
    """Write ``.cursorrules``, ``copilot-instructions.md``, and ``ai-context.json`` (Agent 45, AI Semantic Layer Crew, Phase 5)."""

    name: str = "multi_format_serializer"
    description: str = (
        "Write three AI context output files: .cursorrules, copilot-instructions.md, "
        "and ai-context.json to output_dir. Returns paths of files written."
    )
    args_schema: type[BaseModel] = _MultiFormatSerializerInput

    def _run(
        self,
        cursorrules: str,
        copilot_instructions: str,
        ai_context: dict[str, Any],
        output_dir: str,
        **kwargs: Any,
    ) -> dict[str, str]:
        return serialize_multi_format(cursorrules, copilot_instructions, ai_context, output_dir)
