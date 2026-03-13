"""ProcessDefinitionBuilder — CrewAI BaseTool.

Builds an RFC process definition JSON that encodes when RFCs are required
and what approval criteria apply.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

_MANDATORY_RFC_TRIGGERS = ["new_primitive", "breaking_token_change"]


class _BuilderInput(BaseModel):
    workflow_config: dict[str, Any]


class ProcessDefinitionBuilder(BaseTool):
    """Build an RFC process definition JSON from workflow config."""

    name: str = "process_definition_builder"
    description: str = (
        "Builds an RFC process definition JSON encoding when RFCs are required "
        "and approval criteria. Always includes new_primitive and breaking_token_change "
        "in rfc_required_for."
    )
    args_schema: type[BaseModel] = _BuilderInput

    def _run(self, workflow_config: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        extra_triggers: list[str] = list(workflow_config.get("additional_rfc_triggers", []))
        rfc_required_for = _MANDATORY_RFC_TRIGGERS + [
            t for t in extra_triggers if t not in _MANDATORY_RFC_TRIGGERS
        ]

        requires_approval = workflow_config.get("approval_required", True)

        return {
            "rfc_required_for": rfc_required_for,
            "approval_required": requires_approval,
            "approvers": workflow_config.get("approvers", ["design-system-maintainers"]),
            "review_period_days": workflow_config.get("review_period_days", 7),
        }
