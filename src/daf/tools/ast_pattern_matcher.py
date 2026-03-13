"""Agent 38 – ASTPatternMatcher tool (Release Crew, Phase 6).

Regex/heuristic scan of src/components/**/*.tsx and src/primitives/**/*.tsx.
Detects raw HTML elements (<button, <input, etc.) and hardcoded hex/rgb colors.
Returns {"targets": [{type, pattern, file, line}]} or {"targets": []} when
src/ is absent.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import Field

_RAW_HTML_ELEMENTS = ["button", "input", "select", "textarea", "a", "div", "span"]
_RAW_HTML_PATTERN = re.compile(
    r"<(" + "|".join(_RAW_HTML_ELEMENTS) + r")[\s>/""]",
    re.IGNORECASE,
)
_HEX_COLOR_PATTERN = re.compile(r"#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b")
_RGB_COLOR_PATTERN = re.compile(r"rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)")


class ASTPatternMatcher(BaseTool):
    """Heuristic scan of TSX source for codemod migration patterns."""

    name: str = Field(default="ast_pattern_matcher")
    description: str = Field(
        default=(
            "Scans src/components/**/*.tsx and src/primitives/**/*.tsx for raw HTML "
            "elements and hardcoded hex/rgb colors. Returns {\"targets\": [{type, pattern, "
            "file, line}]} or {\"targets\": []} when src/ is absent."
        )
    )
    output_dir: str = Field(default="")

    def _run(self, _input: str = "", **kwargs: Any) -> dict[str, Any]:
        src_root = Path(self.output_dir) / "src"
        if not src_root.exists():
            return {"targets": []}

        targets: list[dict[str, Any]] = []

        for tsx_file in sorted(src_root.rglob("*.tsx")):
            try:
                lines = tsx_file.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue

            rel_path = str(tsx_file.relative_to(self.output_dir))
            for line_no, line in enumerate(lines, start=1):
                # Check raw HTML elements
                for m in _RAW_HTML_PATTERN.finditer(line):
                    element = m.group(1).lower()
                    targets.append({
                        "type": "raw_html",
                        "pattern": element,
                        "file": rel_path,
                        "line": line_no,
                    })

                # Check hardcoded hex colors
                for m in _HEX_COLOR_PATTERN.finditer(line):
                    targets.append({
                        "type": "hardcoded_color",
                        "pattern": m.group(0),
                        "file": rel_path,
                        "line": line_no,
                    })

                # Check hardcoded rgb colors
                for m in _RGB_COLOR_PATTERN.finditer(line):
                    targets.append({
                        "type": "hardcoded_color",
                        "pattern": m.group(0),
                        "file": rel_path,
                        "line": line_no,
                    })

        return {"targets": targets}
