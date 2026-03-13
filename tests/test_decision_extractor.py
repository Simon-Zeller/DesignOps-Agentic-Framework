"""Tests for decision_extractor.extract_decisions."""
from daf.tools.decision_extractor import extract_decisions


def test_extracts_all_decisions():
    summary = {
        "decisions": [
            {"title": "Token Scale", "context": "Ctx", "decision": "Dec", "consequences": "Con"},
            {"title": "Archetype", "context": "Ctx2", "decision": "Dec2", "consequences": "Con2"},
        ]
    }
    decisions = extract_decisions(summary)
    assert len(decisions) == 2


def test_returns_empty_list_for_no_decisions():
    decisions = extract_decisions({})
    assert decisions == []


def test_each_decision_has_required_keys():
    summary = {"decisions": [{"title": "T", "decision": "D"}]}
    decisions = extract_decisions(summary)
    assert "title" in decisions[0]
    assert "decision" in decisions[0]
    assert "context" in decisions[0]  # defaults to empty string
    assert "consequences" in decisions[0]  # defaults to empty string
