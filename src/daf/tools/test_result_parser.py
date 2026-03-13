"""Agent 39 – TestResultParser tool (Release Crew, Phase 6).

Parses Vitest/pytest stdout into {"passed": N, "failed": N, "skipped": N}.
Returns all-zero dict on empty or unrecognised input.
"""
from __future__ import annotations

import re
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field

# Vitest: "Tests  10 passed (10)" or "Tests  8 passed | 2 failed (10)"
_VITEST_PASSED = re.compile(r"(\d+)\s+passed")
_VITEST_FAILED = re.compile(r"(\d+)\s+failed")
_VITEST_SKIPPED = re.compile(r"(\d+)\s+skipped")

# pytest: "3 passed, 1 failed, 2 skipped"
_PYTEST_SUMMARY = re.compile(
    r"(?:(\d+)\s+passed)?[,\s]*(?:(\d+)\s+failed)?[,\s]*(?:(\d+)\s+skipped)?"
)


class TestResultParser(BaseTool):
    """Parse Vitest/pytest stdout into structured pass/fail summary."""

    name: str = Field(default="test_result_parser")
    description: str = Field(
        default=(
            "Parses test runner stdout (Vitest or pytest) into "
            "{\"passed\": N, \"failed\": N, \"skipped\": N}. "
            "Returns all-zero dict on empty or unrecognised input."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, stdout: str = "", **kwargs: Any) -> dict[str, Any]:
        if not stdout or not stdout.strip():
            return {"passed": 0, "failed": 0, "skipped": 0}

        passed = 0
        failed = 0
        skipped = 0

        m_passed = _VITEST_PASSED.search(stdout)
        m_failed = _VITEST_FAILED.search(stdout)
        m_skipped = _VITEST_SKIPPED.search(stdout)

        if m_passed:
            passed = int(m_passed.group(1))
        if m_failed:
            failed = int(m_failed.group(1))
        if m_skipped:
            skipped = int(m_skipped.group(1))

        if passed == 0 and failed == 0 and skipped == 0:
            return {"passed": 0, "failed": 0, "skipped": 0}

        return {"passed": passed, "failed": failed, "skipped": skipped}
