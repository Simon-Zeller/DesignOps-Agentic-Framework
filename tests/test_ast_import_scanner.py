"""Unit tests for ASTImportScanner tool."""
from __future__ import annotations

from pathlib import Path


def test_ast_import_scanner_returns_empty_for_missing_src_dir(tmp_path):
    """Returns empty imports list when src/ does not exist — no exception raised."""
    from daf.tools.ast_import_scanner import ASTImportScanner

    result = ASTImportScanner()._run(str(tmp_path))
    assert result["imports"] == []


def test_ast_import_scanner_detects_import_in_tsx_file(tmp_path):
    """Detects import statements in a TSX file."""
    from daf.tools.ast_import_scanner import ASTImportScanner

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Button.tsx").write_text('import { Box } from "../primitives/Box";\n')

    result = ASTImportScanner()._run(str(tmp_path))
    assert len(result["imports"]) > 0
    found = any(
        entry["from"] == "Button" and "Box" in entry["imports"]
        for entry in result["imports"]
    )
    assert found


def test_ast_import_scanner_handles_malformed_tsx_without_raising(tmp_path):
    """Malformed TSX files are skipped gracefully; no SyntaxError propagates."""
    from daf.tools.ast_import_scanner import ASTImportScanner

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    # Valid file
    (src_dir / "Good.tsx").write_text('import { Foo } from "./foo";\n')
    # Malformed file — unclosed JSX tag
    (src_dir / "Bad.tsx").write_text("const x = <div>\nunclosed JSX <<<<>>>>\n")

    result = ASTImportScanner()._run(str(tmp_path))
    # Good.tsx should still be scanned
    assert any(entry["from"] == "Good" for entry in result["imports"])
    # No exception raised (test itself verifies this)
