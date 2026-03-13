"""GateEvaluator — CrewAI BaseTool.

Evaluates five quality gates independently for a single component.
Returns a dict of gate_name → pass/fail (bool) per gate.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

_COVERAGE_THRESHOLD = 0.80
_FIVE_GATES = (
    "coverage_80",
    "a11y_zero_critical",
    "no_phantom_refs",
    "has_docs",
    "has_usage_example",
)


def _all_false() -> dict[str, bool]:
    return {gate: False for gate in _FIVE_GATES}


class _EvaluatorInput(BaseModel):
    component: str
    coverage: float = 0.0
    a11y_audit: dict[str, Any] | None = None
    phantom_refs: list[str] = []
    docs_path: str | None = None
    usage_example: str | None = None
    scorecard: dict[str, Any] | None = None


class GateEvaluator(BaseTool):
    """Evaluate five quality gates independently for a single component."""

    name: str = "gate_evaluator"
    description: str = (
        "Evaluates coverage_80, a11y_zero_critical, no_phantom_refs, has_docs, and "
        "has_usage_example gates independently for a given component. Returns all False "
        "if required data is absent."
    )
    args_schema: type[BaseModel] = _EvaluatorInput

    def _run(
        self,
        component: str,
        coverage: float = 0.0,
        a11y_audit: dict[str, Any] | None = None,
        phantom_refs: list[str] | None = None,
        docs_path: str | None = None,
        usage_example: str | None = None,
        scorecard: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, bool]:
        if scorecard is None:
            return _all_false()

        if phantom_refs is None:
            phantom_refs = []

        coverage_pass = coverage >= _COVERAGE_THRESHOLD
        a11y_pass = (
            a11y_audit is not None
            and a11y_audit.get("critical_violations", 1) == 0
        )
        phantom_pass = len(phantom_refs) == 0
        docs_pass = bool(docs_path)
        usage_pass = bool(usage_example)

        return {
            "coverage_80": coverage_pass,
            "a11y_zero_critical": a11y_pass,
            "no_phantom_refs": phantom_pass,
            "has_docs": docs_pass,
            "has_usage_example": usage_pass,
        }
