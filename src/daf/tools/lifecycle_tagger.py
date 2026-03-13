"""LifecycleTagger — CrewAI BaseTool.

Injects ``lifecycle_status`` metadata into a component dict.
Returns a new (deep-copied) dict with the status injected.
"""
from __future__ import annotations

import copy
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


class _TaggerInput(BaseModel):
    component: dict[str, Any]
    status: str


class LifecycleTagger(BaseTool):
    """Inject lifecycle_status into a component dict."""

    name: str = "lifecycle_tagger"
    description: str = (
        "Injects lifecycle_status (stable | beta | experimental) into a component dict. "
        "Returns a deep-copied dict with lifecycle_status added."
    )
    args_schema: type[BaseModel] = _TaggerInput

    def _run(
        self,
        component: dict[str, Any],
        status: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        result = copy.deepcopy(component)
        result["lifecycle_status"] = status
        return result
