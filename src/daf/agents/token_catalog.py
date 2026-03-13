"""Agent 22 — Token Catalog Agent.

Generates ``docs/tokens/catalog.md`` — every token with resolved value,
tier classification, visual representation, and LLM-generated usage context.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from daf.tools.token_value_resolver import resolve_token, classify_tier
from daf.tools.scale_visualizer import visualize_token
from daf.tools.usage_context_extractor import extract_usage_context


def _call_llm(prompt: str) -> str:  # pragma: no cover
    """Placeholder LLM call — patchable in tests."""
    return prompt


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def run_token_catalog(output_dir: str) -> None:
    """Generate the token catalog Markdown file.

    Reads:
        ``{output_dir}/tokens/semantic.tokens.json``
        (also loads other ``*.tokens.json`` files if present)

    Writes:
        ``{output_dir}/docs/tokens/catalog.md``

    Args:
        output_dir: Root pipeline output directory.
    """
    od = Path(output_dir)
    tokens_dir = od / "tokens"

    # Collect all tokens from available token files
    all_tokens: dict[str, str] = {}
    if tokens_dir.exists():
        for token_file in sorted(tokens_dir.glob("*.tokens.json")):
            file_tokens = _load_json(token_file)
            all_tokens.update({k: str(v) for k, v in file_tokens.items()})

    lines: list[str] = [
        "# Token Catalog",
        "",
        "All design tokens with resolved values, tier classification, and usage context.",
        "",
    ]

    if not all_tokens:
        lines.append("*No tokens available.*")
    else:
        lines += [
            "| Token Path | Value | Visual | Tier | Usage Context | Description |",
            "|------------|-------|--------|------|---------------|-------------|",
        ]
        for token_path in sorted(all_tokens):
            value = resolve_token(token_path, all_tokens) or ""
            tier = classify_tier(token_path)
            visual = visualize_token(token_path, value)
            context = extract_usage_context(token_path, {})
            description_prompt = (
                f"In one sentence, describe the design system usage of the token "
                f"'{token_path}' with value '{value}'."
            )
            description = _call_llm(description_prompt) or "(no description)"
            if not description:
                description = "(no description)"
            lines.append(
                f"| {token_path} | {value} | {visual} | {tier} | {context} | {description} |"
            )

    catalog_content = "\n".join(lines)
    _write_file(od / "docs" / "tokens" / "catalog.md", catalog_content)
