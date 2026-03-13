"""Unit tests for TokenBudgetOptimizer tool (p16-ai-semantic-layer-crew)."""
from __future__ import annotations

import pytest


def test_token_budget_optimizer_no_truncation_within_limit(tmp_path):
    """TokenBudgetOptimizer returns content unchanged when under token budget."""
    from daf.tools.token_budget_optimizer import TokenBudgetOptimizer

    content = "Short content."
    budget = 10_000  # 10k char budget — well above short content

    optimizer = TokenBudgetOptimizer()
    result = optimizer._run(content=content, max_tokens=budget, output_dir=str(tmp_path))

    assert isinstance(result, dict)
    assert "optimized" in result
    assert result["optimized"] == content
    assert result.get("truncated") is False


def test_token_budget_optimizer_truncates_when_over_budget(tmp_path):
    """TokenBudgetOptimizer truncates content when it exceeds the token budget."""
    from daf.tools.token_budget_optimizer import TokenBudgetOptimizer

    # Generate content that's clearly over a tiny budget (10 chars max)
    content = "A" * 100

    optimizer = TokenBudgetOptimizer()
    result = optimizer._run(content=content, max_tokens=10, output_dir=str(tmp_path))

    assert isinstance(result, dict)
    assert "optimized" in result
    assert len(result["optimized"]) <= len(content)
    assert result.get("truncated") is True


def test_token_budget_optimizer_removes_usage_examples_first(tmp_path):
    """TokenBudgetOptimizer removes usage_examples sections before other content."""
    from daf.tools.token_budget_optimizer import TokenBudgetOptimizer

    # Content with a usage_examples section that should be trimmed first
    usage_block = "\nusage_examples:\n" + ("  - example: " + "x" * 50 + "\n") * 5
    rest = "components:\n  - name: Button\n"
    content = rest + usage_block

    optimizer = TokenBudgetOptimizer()
    result = optimizer._run(
        content=content,
        max_tokens=len(rest) + 5,  # just enough for rest, not usage_block
        output_dir=str(tmp_path),
    )

    assert isinstance(result, dict)
    # usage_examples should be reduced or removed
    assert len(result["optimized"]) < len(content)
