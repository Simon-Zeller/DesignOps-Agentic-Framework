"""Tests for ASTPatternMatcher tool (p17-release-crew, TDD red phase)."""
from __future__ import annotations

from pathlib import Path


def test_detects_raw_html_elements_in_tsx(tmp_path: Path) -> None:
    """Detects raw <button usage in TSX source files."""
    comp_dir = tmp_path / "src" / "components"
    comp_dir.mkdir(parents=True)
    (comp_dir / "Foo.tsx").write_text(
        "export const Foo = () => <button onClick={handle}>Click</button>;\n"
    )

    from daf.tools.ast_pattern_matcher import ASTPatternMatcher

    matcher = ASTPatternMatcher(output_dir=str(tmp_path))
    result = matcher._run("")
    assert "targets" in result
    target_patterns = [t["pattern"] for t in result["targets"]]
    assert any("button" in p for p in target_patterns)


def test_detects_hardcoded_hex_colors_in_tsx(tmp_path: Path) -> None:
    """Detects hardcoded hex color values in TSX source files."""
    comp_dir = tmp_path / "src" / "components"
    comp_dir.mkdir(parents=True)
    (comp_dir / "Bar.tsx").write_text(
        'const styles = { color: "#333333", background: "#fff" };\n'
    )

    from daf.tools.ast_pattern_matcher import ASTPatternMatcher

    matcher = ASTPatternMatcher(output_dir=str(tmp_path))
    result = matcher._run("")
    assert "targets" in result
    target_patterns = [t["pattern"] for t in result["targets"]]
    assert any("#333333" in p or "hex" in p.lower() for p in target_patterns)


def test_returns_empty_targets_when_src_absent(tmp_path: Path) -> None:
    """Returns {'targets': []} without raising when src/components/ is absent."""
    from daf.tools.ast_pattern_matcher import ASTPatternMatcher

    matcher = ASTPatternMatcher(output_dir=str(tmp_path))
    result = matcher._run("")
    assert result == {"targets": []}
