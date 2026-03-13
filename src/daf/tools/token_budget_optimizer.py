"""Agent 45 – TokenBudgetOptimizer tool (AI Semantic Layer Crew, Phase 5).

Counts tokens (character-based approximation) and applies a priority-ordered
truncation strategy to fit AI context files within configurable limits.

Truncation priority order:
1. Trim ``usage_examples`` sections (lowest signal density)
2. Abbreviate slot descriptions
3. Drop internal-only props
4. Hard truncate to max_tokens
"""
from __future__ import annotations

import re
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

# 1 token ≈ 4 characters (rough approximation used by OpenAI tokenizers)
_CHARS_PER_TOKEN = 4

# Pattern matching YAML/Markdown usage_examples blocks
_USAGE_EXAMPLES_RE = re.compile(
    r"\nusage_examples:.*?(?=\n\S|\Z)",
    re.DOTALL,
)


def _char_budget(max_tokens: int) -> int:
    return max_tokens * _CHARS_PER_TOKEN


def _strip_usage_examples(content: str) -> str:
    """Remove ``usage_examples:`` blocks from content."""
    return _USAGE_EXAMPLES_RE.sub("", content)


def optimize_token_budget(
    content: str,
    max_tokens: int,
    output_dir: str = "",
) -> dict[str, Any]:
    """Apply priority-ordered truncation to fit *content* within *max_tokens*.

    Args:
        content: Text content to optimise.
        max_tokens: Maximum number of approximate tokens allowed.
        output_dir: Root pipeline output directory (unused; kept for API consistency).

    Returns:
        Dict with ``optimized`` (str), ``truncated`` (bool), and
        ``original_tokens`` / ``final_tokens`` (int) keys.
    """
    budget = _char_budget(max_tokens)
    original_len = len(content)
    truncated = False

    if len(content) <= budget:
        return {
            "optimized": content,
            "truncated": False,
            "original_tokens": original_len // _CHARS_PER_TOKEN,
            "final_tokens": original_len // _CHARS_PER_TOKEN,
        }

    # Step 1: Remove usage_examples blocks
    result = _strip_usage_examples(content)
    truncated = len(result) < original_len

    if len(result) <= budget:
        return {
            "optimized": result,
            "truncated": truncated,
            "original_tokens": original_len // _CHARS_PER_TOKEN,
            "final_tokens": len(result) // _CHARS_PER_TOKEN,
        }

    # Step 2: Hard truncate at character boundary
    result = result[:budget]
    return {
        "optimized": result,
        "truncated": True,
        "original_tokens": original_len // _CHARS_PER_TOKEN,
        "final_tokens": len(result) // _CHARS_PER_TOKEN,
    }


class _TokenBudgetOptimizerInput(BaseModel):
    content: str
    max_tokens: int
    output_dir: str = ""


class TokenBudgetOptimizer(BaseTool):
    """Apply priority-ordered truncation to AI context content (Agent 45, AI Semantic Layer Crew, Phase 5)."""

    name: str = "token_budget_optimizer"
    description: str = (
        "Fit AI context content within a configurable token budget using priority-ordered "
        "truncation: remove usage_examples first, then hard-truncate. "
        "Returns {optimized, truncated, original_tokens, final_tokens}."
    )
    args_schema: type[BaseModel] = _TokenBudgetOptimizerInput

    def _run(
        self, content: str, max_tokens: int, output_dir: str = "", **kwargs: Any
    ) -> dict[str, Any]:
        return optimize_token_budget(content, max_tokens, output_dir)
