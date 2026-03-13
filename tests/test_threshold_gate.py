"""Tests for threshold_gate.py."""
from __future__ import annotations

import pytest
from daf.tools.threshold_gate import apply_gate, gate_components


def test_score_gte_70_passes():
    result = apply_gate(score=70.0, threshold=70.0)
    assert result["gate"] == "passed"
    assert result["verdict"] is True


def test_score_lt_70_fails():
    result = apply_gate(score=68.0, threshold=70.0)
    assert result["gate"] == "failed"
    assert result["verdict"] is False


def test_gate_on_component_list_splits_pass_fail():
    scores = [
        {"name": "Button", "composite": 85.0},
        {"name": "DatePicker", "composite": 60.0},
        {"name": "Badge", "composite": 72.0},
    ]
    result = gate_components(scores, threshold=70.0)
    assert "Button" in result["passed"]
    assert "Badge" in result["passed"]
    assert "DatePicker" in result["failed"]


def test_perfect_score_passes():
    result = apply_gate(score=100.0, threshold=70.0)
    assert result["gate"] == "passed"
    assert result["verdict"] is True


def test_zero_score_fails():
    result = apply_gate(score=0.0, threshold=70.0)
    assert result["gate"] == "failed"
    assert result["verdict"] is False
