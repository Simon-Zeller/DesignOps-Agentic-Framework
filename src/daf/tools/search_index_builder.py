"""Tool: search_index_builder — chunks Markdown into full-text search index entries."""
from __future__ import annotations

import re


def build_index_entries(markdown_content: str, file_path: str) -> list[dict[str, str]]:
    """Split a Markdown document into heading-paragraph index entries.

    Each H1 or H2 heading creates a new entry. The content following each
    heading (up to the next heading) is stripped of Markdown formatting and
    stored as searchable text.

    Args:
        markdown_content: The raw Markdown string to index.
        file_path: The relative path to the source file (used for ``path``
            and ``id`` fields).

    Returns:
        A list of entry dicts, each with ``id``, ``title``, ``content``,
        and ``path``. Returns an empty list for empty input.
    """
    if not markdown_content.strip():
        return []

    # Split on H1/H2 headings
    sections = re.split(r"\n(?=#{1,2} )", markdown_content)

    entries: list[dict[str, str]] = []
    for idx, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        lines = section.splitlines()
        heading_line = lines[0] if lines else ""

        # Extract heading text
        title = re.sub(r"^#{1,3}\s+", "", heading_line).strip()
        if not title:
            continue

        body_lines = lines[1:]
        body = " ".join(body_lines).strip()

        content = _strip_markdown(body)
        if not content:
            content = _strip_markdown(title)

        entry_id = f"{file_path}#{idx}"
        entries.append(
            {
                "id": entry_id,
                "title": title,
                "content": content,
                "path": file_path,
            }
        )

    return entries


def _strip_markdown(text: str) -> str:
    """Remove common Markdown formatting characters from text."""
    # Remove backtick code spans
    text = re.sub(r"`[^`]*`", "", text)
    # Remove bold/italic markers
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"_+", "", text)
    # Remove heading markers at start of line
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove links [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
