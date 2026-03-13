"""Report Writer — serialises structured generation results to reports/generation-summary.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_generation_summary(
    results: list[dict[str, Any]],
    output_dir: str,
) -> None:
    """Write *results* to ``<output_dir>/reports/generation-summary.json``.

    Creates ``reports/`` if it does not exist. Always writes — even if all
    components failed.

    Args:
        results: List of per-component result dicts. Each should have
                 ``component``, ``files_written``, ``confidence``, and ``warnings``.
        output_dir: Root output directory.
    """
    reports_dir = Path(output_dir) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    total = len(results)
    generated = sum(1 for r in results if r.get("files_written"))
    failed = total - generated

    summary: dict[str, Any] = {
        "total_components": total,
        "generated": generated,
        "failed": failed,
        "components": results,
    }

    output_path = reports_dir / "generation-summary.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
