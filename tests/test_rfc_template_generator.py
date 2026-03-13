"""Tests for rfc_template_generator tool (BaseTool)."""
from __future__ import annotations


def test_generated_template_contains_required_sections():
    """Generated RFC template contains ## Summary, ## Motivation, ## Detailed Design."""
    from daf.tools.rfc_template_generator import RFCTemplateGenerator

    gen = RFCTemplateGenerator()
    process_config = {"rfc_required_for": ["new_primitive", "breaking_token_change"]}
    result = gen._run(process_config=process_config)

    assert "## Summary" in result
    assert "## Motivation" in result
    assert "## Detailed Design" in result


def test_template_generation_is_idempotent():
    """Two calls with identical config produce identical output."""
    from daf.tools.rfc_template_generator import RFCTemplateGenerator

    gen = RFCTemplateGenerator()
    process_config = {"rfc_required_for": ["new_primitive"]}
    result1 = gen._run(process_config=process_config)
    result2 = gen._run(process_config=process_config)

    assert result1 == result2
