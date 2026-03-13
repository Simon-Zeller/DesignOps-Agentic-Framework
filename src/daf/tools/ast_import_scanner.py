"""ASTImportScanner — scans TSX files for import statements using regex.

Returns a dict ``{"imports": [{"from": <component>, "imports": [<name>, ...]}]}``.
Skips malformed files without raising.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

_IMPORT_RE = re.compile(
    r"""import\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"]""",
    re.MULTILINE,
)


def scan_imports(output_dir: str) -> dict[str, Any]:
    """Scan all TSX files under *output_dir*/src/ for import statements.

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        Dict with ``imports`` key — list of ``{"from": stem, "imports": [names]}``.
    """
    src_root = Path(output_dir) / "src"
    results: list[dict[str, Any]] = []

    if not src_root.exists():
        return {"imports": results}

    for tsx_file in src_root.rglob("*.tsx"):
        try:
            source = tsx_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        try:
            matches = _IMPORT_RE.findall(source)
        except Exception:  # noqa: BLE001
            continue

        if matches:
            names = [n.strip() for group, _ in matches for n in group.split(",") if n.strip()]
            results.append({
                "from": tsx_file.stem,
                "imports": names,
            })

    return {"imports": results}


class _ScannerInput(BaseModel):
    output_dir: str


class ASTImportScanner(BaseTool):
    """Scan TSX files for import statements and return per-file import lists."""

    name: str = "ast_import_scanner"
    description: str = (
        "Scan all TSX files in <output_dir>/src/ for import statements. "
        "Returns {imports: [{from, imports}]}. Skips malformed files."
    )
    args_schema: type[BaseModel] = _ScannerInput

    def _run(self, output_dir: str, **kwargs: Any) -> dict[str, Any]:
        return scan_imports(output_dir)
