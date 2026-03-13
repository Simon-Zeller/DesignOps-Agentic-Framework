"""Unit tests for PipelineStageTracker tool."""
from __future__ import annotations


def test_pipeline_stage_tracker_fully_complete_component(tmp_path):
    """Component with all stages present has completeness_score=1.0 and stuck_at=None."""
    from daf.tools.pipeline_stage_tracker import PipelineStageTracker

    # spec
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "button.spec.yaml").write_text("name: Button\n")

    # code
    src_dir = tmp_path / "src" / "components"
    src_dir.mkdir(parents=True)
    (src_dir / "Button.tsx").write_text("export const Button = () => null;\n")

    # tests
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "Button.test.tsx").write_text("test('button', () => {});\n")

    # docs
    docs_dir = tmp_path / "docs" / "components"
    docs_dir.mkdir(parents=True)
    (docs_dir / "button.md").write_text("# Button\n")

    # a11y marker
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "a11y-audit.json").write_text('{"Button": {"passed": true}}')

    result = PipelineStageTracker()._run(str(tmp_path), ["Button"])
    button = next(c for c in result["components"] if c["name"] == "Button")
    assert button["completeness_score"] == 1.0
    assert button["stuck_at"] is None


def test_pipeline_stage_tracker_component_stuck_at_code_generated(tmp_path):
    """Component with spec but no TSX is stuck_at code_generated."""
    from daf.tools.pipeline_stage_tracker import PipelineStageTracker

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "datepicker.spec.yaml").write_text("name: DatePicker\n")

    result = PipelineStageTracker()._run(str(tmp_path), ["DatePicker"])
    dp = next(c for c in result["components"] if c["name"] == "DatePicker")
    assert dp["stuck_at"] == "code_generated"
    assert dp["completeness_score"] < 1.0


def test_pipeline_stage_tracker_empty_component_list(tmp_path):
    """Empty component list produces an empty components array."""
    from daf.tools.pipeline_stage_tracker import PipelineStageTracker

    result = PipelineStageTracker()._run(str(tmp_path), [])
    assert result["components"] == []
