"""RFCTemplateGenerator — CrewAI BaseTool.

Generates a Markdown RFC template with required sections.
"""
from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

_RFC_TEMPLATE = """\
# RFC: [Title]

## Summary

<!-- One-paragraph summary of the proposed change. -->

## Motivation

<!-- Why is this change needed? What problem does it solve? -->

## Detailed Design

<!-- Technical details of the proposed implementation. -->

## Drawbacks

<!-- What are the disadvantages of this approach? -->

## Alternatives

<!-- What other approaches were considered? -->

## Unresolved Questions

<!-- What aspects of the design are still uncertain? -->
"""


class _TemplateInput(BaseModel):
    process_config: dict[str, Any]


class RFCTemplateGenerator(BaseTool):
    """Generate an RFC Markdown template with required sections."""

    name: str = "rfc_template_generator"
    description: str = (
        "Generates a Markdown RFC template containing all required sections "
        "(Summary, Motivation, Detailed Design, Drawbacks, Alternatives, Unresolved Questions)."
    )
    args_schema: type[BaseModel] = _TemplateInput

    def _run(self, process_config: dict[str, Any], **kwargs: Any) -> str:
        return _RFC_TEMPLATE
