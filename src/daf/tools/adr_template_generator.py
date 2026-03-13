"""Tool: adr_template_generator — generates ADR Markdown and slugifies titles."""
from __future__ import annotations

import re
from typing import Any


def generate_adr(decision: dict[str, Any]) -> str:
    """Generate an Architecture Decision Record in standard Markdown format.

    Format: ``# ADR: {title}\\n\\n## Context\\n...\\n\\n## Decision\\n...\\n\\n## Consequences\\n...``

    Args:
        decision: Dict with keys ``title``, ``context``, ``decision``,
            ``consequences``.

    Returns:
        A Markdown string following the ADR template.
    """
    title = decision.get("title", "")
    context = decision.get("context", "")
    decision_text = decision.get("decision", "")
    consequences = decision.get("consequences", "")

    return (
        f"# ADR: {title}\n\n"
        f"## Context\n\n{context}\n\n"
        f"## Decision\n\n{decision_text}\n\n"
        f"## Consequences\n\n{consequences}\n"
    )


def slugify_title(title: str) -> str:
    """Convert a decision title to a kebab-case filename slug.

    Rules:
    - Lowercase
    - Spaces → dashes
    - Non-alphanumeric characters (except dashes) stripped
    - Multiple consecutive dashes collapsed to one

    Args:
        title: The decision title string.

    Returns:
        A kebab-case slug suitable for use as a filename.
    """
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")
