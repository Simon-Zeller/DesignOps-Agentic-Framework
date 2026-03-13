"""Tests for workflow_state_machine tool."""
from __future__ import annotations

import json


def test_token_change_pipeline_contains_gate_check_state():
    """State machine output contains both pipelines with at least one gate check."""
    from daf.tools.workflow_state_machine import generate

    quality_gates = {"minCompositeScore": 70, "a11yLevel": "AA"}
    result = generate(quality_gates)

    assert "token_change_pipeline" in result
    assert "component_change_pipeline" in result

    # At least one state in either pipeline has a non-null gate_check
    all_states = list(result["token_change_pipeline"].values()) + list(
        result["component_change_pipeline"].values()
    )
    assert any(s.get("gate_check") is not None for s in all_states)


def test_empty_quality_gates_produces_null_gate_checks():
    """Empty quality gates config produces workflow with null gate_checks."""
    from daf.tools.workflow_state_machine import generate

    result = generate({})

    assert "token_change_pipeline" in result
    assert "component_change_pipeline" in result

    all_states = list(result["token_change_pipeline"].values()) + list(
        result["component_change_pipeline"].values()
    )
    assert all(s.get("gate_check") is None for s in all_states)


def test_output_is_json_serializable():
    """workflow_state_machine output is JSON-serializable."""
    from daf.tools.workflow_state_machine import generate

    result = generate({"minCompositeScore": 70, "a11yLevel": "AA"})
    # Should not raise TypeError
    json.dumps(result)
