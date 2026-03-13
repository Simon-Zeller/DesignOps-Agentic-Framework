"""GateMapper — maps quality gate IDs to workflow state transition guards.

Given a workflow state machine dict and a list of gate IDs, produces a
mapping of gate ID → list of workflow state names where that gate is checked.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def map_gates(
    workflow: dict[str, Any],
    gates: list[str],
) -> dict[str, list[str]]:
    """Map gate IDs to workflow state names where they appear as gate checks.

    Args:
        workflow: State machine dict with ``token_change_pipeline`` and
            ``component_change_pipeline`` keys.
        gates: List of gate ID strings to map (e.g. ``["coverage_80"]``).

    Returns:
        Mapping of gate ID → list of state names where it appears as
        ``gate_check``.
    """
    result: dict[str, list[str]] = {gate: [] for gate in gates}

    for _pipeline_name, pipeline in workflow.items():
        if not isinstance(pipeline, dict):
            continue
        for state_name, state_data in pipeline.items():
            if not isinstance(state_data, dict):
                continue
            gate_check = state_data.get("gate_check")
            if gate_check in result:
                result[gate_check].append(state_name)

    return result


class _GateMapperInput(BaseModel):
    workflow: dict[str, Any]
    gates: list[str]


class GateMapper(BaseTool):
    """Map quality gate IDs to workflow state transition guards."""

    name: str = "gate_mapper"
    description: str = (
        "Maps gate IDs to the workflow state names where they appear as gate checks. "
        "Returns a dict of gate_id → list of state names."
    )
    args_schema: type[BaseModel] = _GateMapperInput

    def _run(
        self,
        workflow: dict[str, Any],
        gates: list[str],
        **kwargs: Any,
    ) -> dict[str, list[str]]:
        return map_gates(workflow, gates)
