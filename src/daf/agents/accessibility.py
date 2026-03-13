"""Accessibility Agent (Agent 19, Component Factory Crew).

Applies ARIA patches and keyboard scaffolding to TSX components, validates
with TypeScript compiler, and appends accessibility test blocks. Self-corrects
up to 3 times on TSC failures, then restores the original source.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from daf.tools.aria_generator import generate_aria_patches
from daf.tools.focus_trap_validator import validate_focus_trap


_MAX_TSC_RETRIES = 3


def _call_llm(prompt: str) -> str:  # pragma: no cover
    """Placeholder LLM call — patchable in tests."""
    return prompt


def _run_tsc(tsx_path: str) -> tuple[int, str]:  # pragma: no cover
    """Run TypeScript compiler on *tsx_path*. Returns (exit_code, stderr)."""
    result = subprocess.run(
        ["npx", "tsc", "--noEmit", "--jsx", "react", tsx_path],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stderr


def _component_type_from_name(name: str) -> str:
    """Infer ARIA component type from the component name."""
    lower = name.lower()
    if "dialog" in lower or "modal" in lower:
        return "dialog"
    if "menu" in lower:
        return "menu"
    if "tab" in lower:
        return "tabs"
    if "combo" in lower or "select" in lower:
        return "combobox"
    if "listbox" in lower or "list" in lower:
        return "listbox"
    return "button"


def _build_a11y_test_block(name: str, patches: list[dict[str, Any]]) -> str:
    """Build an accessibility describe block for *patches*."""
    lines = [
        "    it('has {}', () => {{}}); // TODO: implement".format(p.get("attribute", "aria attr"))
        for p in patches
    ]
    patch_descriptions = "\n".join(lines) or "    it('meets accessibility requirements', () => {});"
    return (
        f"\ndescribe('{name} Accessibility', () => {{\n"
        f"{patch_descriptions}\n"
        f"}});\n"
    )


def run_accessibility_enforcement(output_dir: str) -> dict[str, Any]:
    """Enforce ARIA, keyboard, and focus-trap requirements on TSX components.

    Reads:
        ``{output_dir}/brand-profile.json``
        ``{output_dir}/src/components/*.tsx`` (and matching *.test.tsx)

    Writes:
        Modified ``*.tsx`` files (in-place, with ARIA patches applied)
        ``{output_dir}/reports/a11y-audit.json``

    Args:
        output_dir: Root pipeline output directory.

    Returns:
        A dict with per-component audit results.
    """
    od = Path(output_dir)
    src_dir = od / "src" / "components"
    reports_dir = od / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Load brand profile
    brand: dict[str, Any] = {}
    brand_path = od / "brand-profile.json"
    if brand_path.exists():
        brand = json.loads(brand_path.read_text(encoding="utf-8"))

    components: dict[str, Any] = {}

    tsx_files = sorted(src_dir.glob("*.tsx")) if src_dir.exists() else []
    tsx_files = [f for f in tsx_files if ".test." not in f.name and ".stories." not in f.name]

    for tsx_file in tsx_files:
        name = tsx_file.stem
        original_source = tsx_file.read_text(encoding="utf-8")
        component_type = _component_type_from_name(name)

        # Generate ARIA patches
        spec: dict[str, Any] = {}
        patches = generate_aria_patches(spec, component_type)

        # Ask LLM to apply patches to the source
        prompt = (
            f"Apply these ARIA patches to the following TSX component '{name}':\n"
            f"Patches: {json.dumps(patches)}\n\n"
            f"Source:\n{original_source}\n\n"
            "Return ONLY the updated TSX source code."
        )
        patched_source = _call_llm(prompt)

        # Validate with TSC (self-correct up to _MAX_TSC_RETRIES times)
        patch_failed = False
        aria_patched = False
        tsc_errors: list[str] = []

        if patched_source != original_source:
            for attempt in range(_MAX_TSC_RETRIES):
                tsx_file.write_text(patched_source, encoding="utf-8")
                exit_code, stderr = _run_tsc(str(tsx_file))
                if exit_code == 0:
                    aria_patched = True
                    break
                tsc_errors.append(stderr)
                if attempt < _MAX_TSC_RETRIES - 1:
                    # Ask LLM to fix the TSC error
                    fix_prompt = (
                        f"The following TypeScript error occurred after patching '{name}':\n"
                        f"{stderr}\n\nPlease fix the TSX source:\n{patched_source}\n"
                        "Return ONLY the corrected TSX source."
                    )
                    patched_source = _call_llm(fix_prompt)
            else:
                # All retries exhausted — restore original
                tsx_file.write_text(original_source, encoding="utf-8")
                patch_failed = True
        else:
            # LLM returned same source = no patches needed / no changes
            aria_patched = False

        # Validate focus trap
        focus_result = validate_focus_trap(tsx_file.read_text(encoding="utf-8"), component_type)

        # Determine a11y pass rate
        issues: list[str] = []
        if patch_failed:
            issues.append("aria_patch_failed_tsc")
        if not focus_result.get("not_applicable") and not focus_result.get("focus_trap_present"):
            issues.extend(focus_result.get("issues", []))

        a11y_pass_rate = 1.0 if not issues else max(0.0, 1.0 - len(issues) * 0.25)

        components[name] = {
            "aria_patched": aria_patched,
            "patch_failed": patch_failed,
            "a11y_pass_rate": a11y_pass_rate,
            "issues": issues,
            "tsc_errors": tsc_errors if tsc_errors else None,
        }

        # Append accessibility test block to .test.tsx
        test_file = src_dir / f"{name}.test.tsx"
        if test_file.exists():
            test_content = test_file.read_text(encoding="utf-8")
            a11y_block = _build_a11y_test_block(name, patches)
            placeholder = "// @accessibility-placeholder"
            if placeholder in test_content:
                test_content = test_content.replace(placeholder, a11y_block)
            else:
                test_content = test_content.rstrip() + "\n" + a11y_block
            test_file.write_text(test_content, encoding="utf-8")

    audit: dict[str, Any] = {"components": components, "a11y_level": brand.get("a11y_level", "AA")}
    (reports_dir / "a11y-audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )

    _call_llm(f"Accessibility enforcement complete for {len(components)} component(s).")
    return audit
