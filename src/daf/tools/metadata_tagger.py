"""Tool: metadata_tagger — assigns category metadata to search index entries."""
from __future__ import annotations


def tag_entry(entry: dict[str, str], file_path: str) -> dict[str, str]:
    """Assign a ``category`` field to an index entry based on its file path.

    Category rules:
    - Path contains ``components/`` → ``"component"``
    - Path contains ``tokens/`` → ``"token"``
    - Path contains ``decisions/`` → ``"decision"``
    - Path ends with ``README.md`` → ``"readme"``
    - Everything else → ``"other"``

    Args:
        entry: The index entry dict (will be copied, not mutated).
        file_path: The relative or absolute path to the source doc file.

    Returns:
        A new dict with a ``category`` key added.
    """
    normalized = file_path.replace("\\", "/")

    if "components/" in normalized:
        category = "component"
    elif "tokens/" in normalized:
        category = "token"
    elif "decisions/" in normalized:
        category = "decision"
    elif normalized.endswith("README.md"):
        category = "readme"
    else:
        category = "other"

    return {**entry, "category": category}
