"""Tests for lifecycle_tagger tool (BaseTool)."""
from __future__ import annotations


def test_lifecycle_tagger_injects_status():
    """LifecycleTagger._run injects lifecycle_status into component dict."""
    from daf.tools.lifecycle_tagger import LifecycleTagger

    tagger = LifecycleTagger()
    component = {"name": "Button", "version": "1.0"}
    result = tagger._run(component=component, status="experimental")

    assert result["lifecycle_status"] == "experimental"
    assert result["name"] == "Button"


def test_lifecycle_tagger_does_not_mutate_input():
    """LifecycleTagger._run does not mutate the input dict."""
    from daf.tools.lifecycle_tagger import LifecycleTagger

    tagger = LifecycleTagger()
    component = {"name": "Card"}
    tagger._run(component=component, status="stable")

    assert "lifecycle_status" not in component
