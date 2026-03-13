"""Agent 25 — Search Index Agent.

Builds ``docs/search-index.json`` — a full-text searchable index across all
generated docs. Fully deterministic: no LLM involved.
"""
from __future__ import annotations

import json
from pathlib import Path

from daf.tools.search_index_builder import build_index_entries
from daf.tools.metadata_tagger import tag_entry


def run_search_index(output_dir: str) -> None:
    """Build the full-text search index from all doc Markdown files.

    Reads:
        ``{output_dir}/docs/**/*.md``

    Writes:
        ``{output_dir}/docs/search-index.json``

    Args:
        output_dir: Root pipeline output directory.
    """
    od = Path(output_dir)
    docs_dir = od / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    all_entries: list[dict[str, str]] = []

    md_files = sorted(docs_dir.rglob("*.md")) if docs_dir.exists() else []

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        # Use a consistent relative path for indexing
        try:
            rel_path = str(md_file.relative_to(od)).replace("\\", "/")
        except ValueError:
            rel_path = str(md_file)

        entries = build_index_entries(content, rel_path)
        for entry in entries:
            tagged = tag_entry(entry, rel_path)
            all_entries.append(tagged)

    (docs_dir / "search-index.json").write_text(
        json.dumps(all_entries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
