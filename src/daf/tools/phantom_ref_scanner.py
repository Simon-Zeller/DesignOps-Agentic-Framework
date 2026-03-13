"""PhantomRefScanner — CrewAI BaseTool.

Identifies references to non-existent tokens. Takes the merged key namespace
(set of all defined token paths) and a references dict {source_path: target_path}.
Returns a list of phantom entries: [{token_path, missing_ref}].
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


class _ScannerInput(BaseModel):
    merged_namespace: set[str]
    references: dict[str, str]


class PhantomRefScanner(BaseTool):
    """Detect references to tokens that do not exist in the merged namespace."""

    name: str = "phantom_ref_scanner"
    description: str = (
        "Scan token references for phantom entries — references to keys that do not "
        "exist in the merged token namespace. Returns [{token_path, missing_ref}]."
    )
    args_schema: type[BaseModel] = _ScannerInput

    def _run(
        self,
        merged_namespace: set[str],
        references: dict[str, str],
        **kwargs: Any,
    ) -> list[dict[str, str]]:
        phantoms: list[dict[str, str]] = []
        for token_path, target in references.items():
            if target not in merged_namespace:
                phantoms.append({
                    "token_path": token_path,
                    "missing_ref": target,
                })
        return phantoms
