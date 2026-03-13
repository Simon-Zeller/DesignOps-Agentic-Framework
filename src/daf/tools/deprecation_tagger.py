"""DeprecationTagger — CrewAI BaseTool.

Injects $extensions.com.daf.deprecated metadata into a specific token in a
nested DTCG token dict. The original token is preserved; only the $extensions
field is augmented.
"""
from __future__ import annotations

import copy
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


class _TaggerInput(BaseModel):
    token_dict: dict[str, Any]
    path: str
    metadata: dict[str, Any]


class DeprecationTagger(BaseTool):
    """Tag a token with $extensions.com.daf.deprecated metadata."""

    name: str = "deprecation_tagger"
    description: str = (
        "Inject $extensions.com.daf.deprecated into a token at the given dot-path. "
        "Returns the updated (deep-copied) token dict."
    )
    args_schema: type[BaseModel] = _TaggerInput

    def _run(
        self,
        token_dict: dict[str, Any],
        path: str,
        metadata: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        result = copy.deepcopy(token_dict)
        parts = path.split(".")
        node = result
        for part in parts:
            if part not in node:
                raise KeyError(f"Path '{path}' not found in token dict at segment '{part}'.")
            node = node[part]

        if "$extensions" not in node:
            node["$extensions"] = {}
        node["$extensions"]["com.daf.deprecated"] = metadata
        return result
