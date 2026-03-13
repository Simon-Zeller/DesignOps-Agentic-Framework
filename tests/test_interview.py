"""Tests for the interview flow and output (TDD red phase)."""

import json


# ---------------------------------------------------------------------------
# Full interview integration tests via CliRunner
# ---------------------------------------------------------------------------

# The interview prompts in order (19 prompts when no session exists):
#  1. Project name
#  2. Archetype (1=enterprise-b2b)
#  3-9. Colors: primary, secondary, neutral, semantic success/warning/error/info
#  10-11. Typography: scaleRatio, baseSize
#  12. Spacing density
#  13. Border radius
#  14. Elevation
#  15. Motion
#  16. Themes
#  17. Accessibility
#  18. Component scope
#  19. Add component overrides? (y/N)

_FULL_INTERVIEW_INPUT = "My Design System\n1\n" + "\n" * 17


def test_full_interview_produces_brand_profile_json(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from daf.cli import app

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "daf.cli.run_first_publish_agent",
        lambda od, **kw: {"pipeline": {"status": "success"}, "phase_results": []},
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["init"], input=_FULL_INTERVIEW_INPUT + "A\n")

    assert result.exit_code == 0, f"Unexpected exit: {result.output}"
    assert (tmp_path / "brand-profile.json").exists()


def test_full_interview_output_is_valid_json(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from daf.cli import app

    monkeypatch.chdir(tmp_path)
    runner = CliRunner(mix_stderr=False)
    runner.invoke(app, ["init"], input=_FULL_INTERVIEW_INPUT)

    content = (tmp_path / "brand-profile.json").read_text()
    data = json.loads(content)
    assert isinstance(data, dict)


def test_full_interview_output_has_all_required_fields(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from daf.cli import app

    required_fields = [
        "name",
        "archetype",
        "colors",
        "typography",
        "spacing",
        "borderRadius",
        "elevation",
        "motion",
        "themes",
        "accessibility",
        "componentScope",
        "breakpoints",
    ]

    monkeypatch.chdir(tmp_path)
    runner = CliRunner(mix_stderr=False)
    runner.invoke(app, ["init"], input=_FULL_INTERVIEW_INPUT)

    data = json.loads((tmp_path / "brand-profile.json").read_text())
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_full_interview_output_is_pretty_printed(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from daf.cli import app

    monkeypatch.chdir(tmp_path)
    runner = CliRunner(mix_stderr=False)
    runner.invoke(app, ["init"], input=_FULL_INTERVIEW_INPUT)

    content = (tmp_path / "brand-profile.json").read_text()
    assert "\n" in content, "Expected pretty-printed JSON (multi-line)"


def test_full_interview_exit_code_zero(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from daf.cli import app

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "daf.cli.run_first_publish_agent",
        lambda od, **kw: {"pipeline": {"status": "success"}, "phase_results": []},
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["init"], input=_FULL_INTERVIEW_INPUT + "A\n")

    assert result.exit_code == 0
    assert "brand-profile.json" in result.output


def test_full_interview_overwrites_existing_profile(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from daf.cli import app

    (tmp_path / "brand-profile.json").write_text(json.dumps({"name": "Old"}))

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "daf.cli.run_first_publish_agent",
        lambda od, **kw: {"pipeline": {"status": "success"}, "phase_results": []},
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["init"], input=_FULL_INTERVIEW_INPUT + "A\n")

    assert result.exit_code == 0
    data = json.loads((tmp_path / "brand-profile.json").read_text())
    assert data["name"] == "My Design System"


# ---------------------------------------------------------------------------
# Unit tests for build_profile and collect_overrides
# ---------------------------------------------------------------------------


def _make_state(**kwargs):

    defaults = {
        "name": "Test DS",
        "archetype": "enterprise-b2b",
        "colors_primary": "#1a73e8",
        "colors_secondary": "#5f6368",
        "colors_neutral": "#f1f3f4",
        "colors_semantic_success": "#34a853",
        "colors_semantic_warning": "#fbbc04",
        "colors_semantic_error": "#ea4335",
        "colors_semantic_info": "#4285f4",
        "typography_scale_ratio": 1.25,
        "typography_base_size": 16,
        "spacing_density": "compact",
        "border_radius": "sm",
        "elevation": "subtle",
        "motion": "reduced",
        "themes": "light,dark",
        "accessibility": "AA",
        "component_scope": "comprehensive",
        "component_overrides": None,
        "last_step": 11,
    }
    defaults.update(kwargs)
    return defaults


def test_build_profile_omits_component_overrides_when_none():
    from daf.interview import InterviewState, build_profile

    state = InterviewState(**_make_state(component_overrides=None))
    profile = build_profile(state)
    assert "componentOverrides" not in profile


def test_build_profile_includes_component_overrides_when_set():
    from daf.interview import InterviewState, build_profile

    overrides = {"Button": {"borderRadius": "4px"}}
    state = InterviewState(**_make_state(component_overrides=overrides))
    profile = build_profile(state)
    assert "componentOverrides" in profile
    assert profile["componentOverrides"] == overrides


def test_collect_overrides_returns_none_when_no_editor(monkeypatch):
    from daf.interview import collect_overrides

    monkeypatch.delenv("EDITOR", raising=False)
    monkeypatch.delenv("VISUAL", raising=False)
    result = collect_overrides()
    assert result is None


# ---------------------------------------------------------------------------
# Session resume and start-over paths
# ---------------------------------------------------------------------------

_ENTERPRISE_SESSION_ANSWERS = {
    "name": "Resuming DS",
    "archetype": "enterprise-b2b",
    "colors_primary": "#1a73e8",
    "colors_secondary": "#5f6368",
    "colors_neutral": "#f1f3f4",
    "colors_semantic_success": "#34a853",
    "colors_semantic_warning": "#fbbc04",
    "colors_semantic_error": "#ea4335",
    "colors_semantic_info": "#4285f4",
    "typography_scale_ratio": 1.25,
    "typography_base_size": 16,
    "spacing_density": "compact",
    "border_radius": "sm",
    "elevation": "subtle",
    "motion": "reduced",
    "themes": "light,dark",
    "accessibility": "AA",
    "component_scope": "comprehensive",
    "component_overrides": None,
    "last_step": 2,
}

# Resume prompt + 17 Enter presses for steps 3-11 defaults
_RESUME_INPUT = "y\n" + "\n" * 17


def test_session_resume_continues_from_last_step(tmp_path, monkeypatch):
    """Resuming an interrupted session picks up from where it left off."""
    from typer.testing import CliRunner

    from daf.cli import app

    session_file = tmp_path / ".daf-session.json"
    session_file.write_text(
        json.dumps({"last_step": 2, "answers": _ENTERPRISE_SESSION_ANSWERS})
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "daf.cli.run_first_publish_agent",
        lambda od, **kw: {"pipeline": {"status": "success"}, "phase_results": []},
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["init"], input=_RESUME_INPUT + "A\n")

    assert result.exit_code == 0, f"Unexpected exit: {result.output}"
    data = json.loads((tmp_path / "brand-profile.json").read_text())
    assert data["name"] == "Resuming DS"


def test_session_start_over_clears_previous_answers(tmp_path, monkeypatch):
    """Choosing 'n' at the resume prompt starts a fresh interview."""
    from typer.testing import CliRunner

    from daf.cli import app

    session_file = tmp_path / ".daf-session.json"
    session_file.write_text(
        json.dumps({"last_step": 2, "answers": _ENTERPRISE_SESSION_ANSWERS})
    )

    start_over_input = "n\n" + _FULL_INTERVIEW_INPUT

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "daf.cli.run_first_publish_agent",
        lambda od, **kw: {"pipeline": {"status": "success"}, "phase_results": []},
    )
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(app, ["init"], input=start_over_input + "A\n")

    assert result.exit_code == 0, f"Unexpected exit: {result.output}"
    data = json.loads((tmp_path / "brand-profile.json").read_text())
    assert data["name"] == "My Design System"
