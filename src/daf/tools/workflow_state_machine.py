"""WorkflowStateMachine — generates state machine definitions for change pipelines.

Produces ``token_change_pipeline`` and ``component_change_pipeline`` state
machine dicts parameterised by quality-gate thresholds from ``pipeline-config.json``.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel


def generate(quality_gates: dict[str, Any]) -> dict[str, Any]:
    """Generate state machine definitions from quality gate thresholds.

    Each pipeline is a dict of ``{state_name: {"gate_check": str | None, "next": str | None}}``.
    When *quality_gates* is empty all ``gate_check`` values are ``None``.

    Args:
        quality_gates: Quality gate thresholds from ``pipeline-config.json``
            (e.g. ``{"minCompositeScore": 70, "a11yLevel": "AA"}``).

    Returns:
        Dict with ``"token_change_pipeline"`` and ``"component_change_pipeline"`` keys.
    """
    has_gates = bool(quality_gates)

    coverage_gate: str | None = "coverage_80" if has_gates else None
    a11y_gate: str | None = "a11y_zero_critical" if has_gates else None

    token_pipeline: dict[str, Any] = {
        "draft": {"gate_check": None, "next": "review"},
        "review": {"gate_check": coverage_gate, "next": "approved"},
        "approved": {"gate_check": a11y_gate, "next": "released"},
        "released": {"gate_check": None, "next": None},
    }

    component_pipeline: dict[str, Any] = {
        "draft": {"gate_check": None, "next": "gate"},
        "gate": {"gate_check": coverage_gate, "next": "done"},
        "done": {"gate_check": None, "next": None},
    }

    return {
        "token_change_pipeline": token_pipeline,
        "component_change_pipeline": component_pipeline,
    }


class _StateMachineInput(BaseModel):
    quality_gates: dict[str, Any]


class WorkflowStateMachine(BaseTool):
    """Generate state machine definitions for token and component change pipelines."""

    name: str = "workflow_state_machine"
    description: str = (
        "Generates token_change_pipeline and component_change_pipeline state machine dicts "
        "from quality gate thresholds. Returns JSON-serializable dict."
    )
    args_schema: type[BaseModel] = _StateMachineInput

    def _run(self, quality_gates: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return generate(quality_gates)
