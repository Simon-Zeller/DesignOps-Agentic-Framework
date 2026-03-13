"""Tests for gate_evaluator tool (BaseTool)."""
from __future__ import annotations


def _make_passing_args():
    return {
        "component": "Button",
        "coverage": 0.85,
        "a11y_audit": {"critical_violations": 0},
        "phantom_refs": [],
        "docs_path": "docs/Button.md",
        "usage_example": "button-example.tsx",
        "scorecard": {"Button": {"composite": 82.0}},
    }


def test_all_gates_pass_for_compliant_component():
    """Component passing all criteria returns all gate values as True."""
    from daf.tools.gate_evaluator import GateEvaluator

    evaluator = GateEvaluator()
    result = evaluator._run(**_make_passing_args())

    assert result["coverage_80"] is True
    assert result["a11y_zero_critical"] is True
    assert result["no_phantom_refs"] is True
    assert result["has_docs"] is True
    assert result["has_usage_example"] is True


def test_coverage_gate_fails_independently():
    """Coverage gate fails when below 80% but other gates remain unaffected."""
    from daf.tools.gate_evaluator import GateEvaluator

    evaluator = GateEvaluator()
    args = _make_passing_args()
    args["component"] = "Navigation"
    args["coverage"] = 0.75
    args["scorecard"] = {"Navigation": {"composite": 80.0}}
    result = evaluator._run(**args)

    assert result["coverage_80"] is False
    assert result["a11y_zero_critical"] is True


def test_missing_a11y_audit_returns_false_not_exception():
    """Missing a11y audit (None) returns False for a11y gate without raising."""
    from daf.tools.gate_evaluator import GateEvaluator

    evaluator = GateEvaluator()
    args = _make_passing_args()
    args["component"] = "Card"
    args["a11y_audit"] = None
    result = evaluator._run(**args)

    assert result["a11y_zero_critical"] is False


def test_all_gates_false_when_scorecard_absent():
    """All gates are False when scorecard is None."""
    from daf.tools.gate_evaluator import GateEvaluator

    evaluator = GateEvaluator()
    args = _make_passing_args()
    args["component"] = "Modal"
    args["scorecard"] = None
    result = evaluator._run(**args)

    assert all(v is False for v in result.values())
