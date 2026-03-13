"""Tests for gate_mapper tool."""
from __future__ import annotations


def test_gate_ids_mapped_to_workflow_transitions():
    """Each gate ID is mapped to one or more workflow state names."""
    from daf.tools.gate_mapper import map_gates

    workflow = {
        "token_change_pipeline": {
            "draft": {"gate_check": None, "next": "review"},
            "review": {"gate_check": "coverage_80", "next": "approved"},
            "approved": {"gate_check": "a11y_zero_critical", "next": "released"},
        },
        "component_change_pipeline": {
            "draft": {"gate_check": None, "next": "gate"},
            "gate": {"gate_check": "coverage_80", "next": "done"},
        },
    }
    gates = ["coverage_80", "a11y_zero_critical"]
    result = map_gates(workflow, gates)

    assert "coverage_80" in result
    assert "a11y_zero_critical" in result
    assert len(result["coverage_80"]) >= 1
    assert len(result["a11y_zero_critical"]) >= 1
