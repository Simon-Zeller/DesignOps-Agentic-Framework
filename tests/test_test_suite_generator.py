"""Tests for test_suite_generator tool (BaseTool)."""
from __future__ import annotations


def test_generated_tokens_suite_contains_describe_block():
    """tokens test suite output contains describe, import, and test/it blocks."""
    from daf.tools.test_suite_generator import TestSuiteGenerator

    gen = TestSuiteGenerator()
    result = gen._run(suite="tokens", components=["Button", "Input"], token_paths=["global.color"])

    assert "describe(" in result
    assert "import" in result
    assert "test(" in result or "it(" in result


def test_kebab_case_sanitized_to_camel_case():
    """Component names with hyphens are sanitized to camelCase identifiers."""
    from daf.tools.test_suite_generator import TestSuiteGenerator

    gen = TestSuiteGenerator()
    result = gen._run(suite="tokens", components=["date-picker"], token_paths=[])

    assert "datePicker" in result
    assert "date-picker" in result


def test_empty_component_list_produces_valid_typescript():
    """Empty component list still produces a non-empty valid TypeScript structure."""
    from daf.tools.test_suite_generator import TestSuiteGenerator

    gen = TestSuiteGenerator()
    for suite in ("tokens", "a11y", "composition", "compliance"):
        result = gen._run(suite=suite, components=[], token_paths=[])
        assert isinstance(result, str)
        assert len(result) > 0
        assert "describe(" in result or "import" in result
