"""Tests for domain_classifier tool."""
from __future__ import annotations


DOMAINS = {
    "forms": ["input", "button", "select", "checkbox"],
    "navigation": ["breadcrumb", "nav", "menu", "tab"],
    "data-display": ["datagrid", "table", "grid", "chart"],
    "layout": ["card", "panel", "container"],
}


def test_component_classified_by_keyword_match():
    """Standard components are classified into correct domains by keyword."""
    from daf.tools.domain_classifier import classify

    result = classify(["Button", "Breadcrumb"], DOMAINS)
    assert result["Button"] == "forms"
    assert result["Breadcrumb"] == "navigation"


def test_multi_domain_component_assigned_to_highest_score():
    """DataGrid matches data-display (higher score) over forms."""
    from daf.tools.domain_classifier import classify

    domains = {
        "data-display": ["datagrid", "data", "grid"],
        "forms": ["grid"],
    }
    result = classify(["DataGrid"], domains)
    assert result["DataGrid"] == "data-display"


def test_unmatched_component_is_orphan():
    """A component with no domain match is classified as __orphan__."""
    from daf.tools.domain_classifier import classify

    result = classify(["MegaMenu"], DOMAINS)
    assert result["MegaMenu"] == "__orphan__"


def test_empty_component_list_returns_empty_dict():
    """Empty component list returns empty dict without error."""
    from daf.tools.domain_classifier import classify

    result = classify([], DOMAINS)
    assert result == {}
