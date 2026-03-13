"""TokenComplianceScannerTool — wraps compute_token_compliance for crew-scope use.

Delegates all scanning logic to ``compute_token_compliance`` from
``daf.tools.composition_rule_engine``; no scanning logic is re-implemented here.

Runs the compliance check across all TSX files in ``<output_dir>/src/`` and
returns a per-file report with a roll-up summary.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from daf.tools.composition_rule_engine import compute_token_compliance


def scan_compliance(output_dir: str) -> dict[str, Any]:
    """Run token compliance scan across all TSX files.

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        Dict with ``files`` (per-file results) and ``summary`` (aggregated stats).
    """
    od = Path(output_dir)
    src_root = od / "src"
    files: list[dict[str, Any]] = []

    if src_root.exists():
        for tsx_file in src_root.rglob("*.tsx"):
            try:
                source = tsx_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            result = compute_token_compliance(source)
            files.append({
                "file": str(tsx_file.relative_to(od)),
                **result,
            })

    total_hardcoded = sum(f["hardcoded_values"] for f in files)
    total_style = sum(f["total_style_values"] for f in files)
    compliance_score = round(
        (total_style - total_hardcoded) / total_style if total_style > 0 else 1.0,
        6,
    )

    return {
        "files": files,
        "summary": {
            "total_violations": total_hardcoded,
            "compliance_score": compliance_score,
        },
    }


class _ScannerInput(BaseModel):
    output_dir: str


class TokenComplianceScannerTool(BaseTool):
    """Scan all TSX files for hardcoded style values using compute_token_compliance."""

    name: str = "token_compliance_scanner"
    description: str = (
        "Scan all TSX files in <output_dir>/src/ for hardcoded colour/spacing values "
        "using compute_token_compliance. Returns {files, summary}."
    )
    args_schema: type[BaseModel] = _ScannerInput

    def _run(self, output_dir: str, **kwargs: Any) -> dict[str, Any]:
        return scan_compliance(output_dir)
