"""Tests for state_machine_validator.py."""
from __future__ import annotations

import pytest
from daf.tools.state_machine_validator import validate_state_machine


def test_valid_state_graph_passes():
    states = {
        "default": {"transitions": ["hover", "focused"]},
        "hover": {"transitions": ["default", "focused"]},
        "focused": {"transitions": ["default", "disabled"]},
        "disabled": {"transitions": [], "terminal": True},
    }
    result = validate_state_machine(states)
    assert result["valid"] is True
    assert result["invalid_transitions"] == []
    assert result["unreachable_states"] == []


def test_terminal_state_with_outgoing_transition_detected():
    states = {
        "default": {"transitions": ["disabled"]},
        "disabled": {"terminal": True, "transitions": ["active"]},
        "active": {"transitions": ["default"]},
    }
    result = validate_state_machine(states)
    assert result["valid"] is False
    bad = result["invalid_transitions"]
    assert any(t["from"] == "disabled" and t["to"] == "active" for t in bad)


def test_unreachable_state_flagged():
    states = {
        "default": {"transitions": ["hover"]},
        "hover": {"transitions": ["default"]},
        "ghost": {"transitions": []},  # no incoming edges
    }
    result = validate_state_machine(states)
    assert "ghost" in result["unreachable_states"]
