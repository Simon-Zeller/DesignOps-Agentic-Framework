"""Unit tests for StructuralComparator tool."""
from __future__ import annotations


def test_structural_comparator_detects_prop_in_spec_and_code_missing_from_docs(tmp_path):
    """Drift item returned when prop is in spec+code but absent from docs."""
    from daf.tools.structural_comparator import StructuralComparator

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text(
        "name: Button\nprops:\n  - name: disabled\n    type: boolean\n"
    )

    src_dir = tmp_path / "src" / "components"
    src_dir.mkdir(parents=True)
    (src_dir / "Button.tsx").write_text(
        "interface ButtonProps { disabled?: boolean; }\n"
    )

    docs_dir = tmp_path / "docs" / "components"
    docs_dir.mkdir(parents=True)
    (docs_dir / "button.md").write_text("# Button\n\n## Props\n\n| Name | Type |\n|------|------|\n")

    result = StructuralComparator()._run(str(tmp_path))
    drift_items = result["drift"]
    found = any(
        item["prop"] == "disabled"
        and item["in_spec"] is True
        and item["in_code"] is True
        and item["in_docs"] is False
        for item in drift_items
    )
    assert found


def test_structural_comparator_detects_prop_in_spec_missing_from_code(tmp_path):
    """Drift item returned when prop is in spec but absent from code."""
    from daf.tools.structural_comparator import StructuralComparator

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text(
        "name: Button\nprops:\n  - name: loading\n    type: boolean\n"
    )

    src_dir = tmp_path / "src" / "components"
    src_dir.mkdir(parents=True)
    (src_dir / "Button.tsx").write_text(
        "interface ButtonProps { variant?: string; }\n"
    )

    docs_dir = tmp_path / "docs" / "components"
    docs_dir.mkdir(parents=True)
    (docs_dir / "button.md").write_text(
        "# Button\n\n## Props\n\n| Name | Type |\n|------|------|\n| loading | boolean |\n"
    )

    result = StructuralComparator()._run(str(tmp_path))
    drift_items = result["drift"]
    found = any(
        item["prop"] == "loading"
        and item["in_spec"] is True
        and item["in_code"] is False
        for item in drift_items
    )
    assert found


def test_structural_comparator_no_drift_for_consistent_component(tmp_path):
    """No drift returned when spec, code, and docs describe the same props."""
    from daf.tools.structural_comparator import StructuralComparator

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text(
        "name: Button\nprops:\n  - name: variant\n    type: string\n"
    )

    src_dir = tmp_path / "src" / "components"
    src_dir.mkdir(parents=True)
    (src_dir / "Button.tsx").write_text(
        "interface ButtonProps { variant?: string; }\n"
    )

    docs_dir = tmp_path / "docs" / "components"
    docs_dir.mkdir(parents=True)
    (docs_dir / "button.md").write_text(
        "# Button\n\n## Props\n\n| Name | Type |\n|------|------|\n| variant | string |\n"
    )

    result = StructuralComparator()._run(str(tmp_path))
    # No drift items where prop is missing from any of the three sources
    missing = [
        item for item in result["drift"]
        if item.get("component", "").lower() == "button"
        and not (item["in_spec"] and item["in_code"] and item["in_docs"])
    ]
    assert missing == []


def test_structural_comparator_handles_missing_markdown_file(tmp_path):
    """Comparator runs without error when Markdown doc does not exist."""
    from daf.tools.structural_comparator import StructuralComparator

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text(
        "name: Button\nprops:\n  - name: variant\n    type: string\n"
    )

    src_dir = tmp_path / "src" / "components"
    src_dir.mkdir(parents=True)
    (src_dir / "Button.tsx").write_text("interface ButtonProps { variant?: string; }\n")

    # No docs directory created

    result = StructuralComparator()._run(str(tmp_path))
    assert "drift" in result
