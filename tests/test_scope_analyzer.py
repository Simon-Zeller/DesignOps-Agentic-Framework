"""Unit tests for scope_analyzer — primitive / simple / complex classification."""
from __future__ import annotations


def test_primitive_classification_by_known_name():
    """A spec with component: Box and no variants or state returns 'primitive'."""
    from daf.tools.scope_analyzer import classify_component

    spec = {"component": "Box"}
    assert classify_component(spec) == "primitive"


def test_complex_classification_by_variant_count():
    """A spec with 5+ variants returns 'complex'."""
    from daf.tools.scope_analyzer import classify_component

    spec = {"component": "DataGrid", "variants": ["a", "b", "c", "d", "e"]}
    assert classify_component(spec) == "complex"


def test_simple_classification_for_under_threshold_component():
    """A spec with 2 variants and no state field returns 'simple'."""
    from daf.tools.scope_analyzer import classify_component

    spec = {"component": "Badge", "variants": ["primary", "secondary"]}
    assert classify_component(spec) == "simple"
