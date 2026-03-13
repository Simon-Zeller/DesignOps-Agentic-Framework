import json

from typer.testing import CliRunner

from daf.cli import app

runner = CliRunner(mix_stderr=False)

# ---------------------------------------------------------------------------
# Existing regression anchors (updated for P02 real behavior)
# ---------------------------------------------------------------------------

_FULL_INTERVIEW_INPUT = "My Design System\n1\n" + "\n" * 17


def test_init_interactive_exits_zero(tmp_path, monkeypatch):
    """Full interactive interview completes successfully with simulated input."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"], input=_FULL_INTERVIEW_INPUT)
    assert result.exit_code == 0, f"Unexpected exit: {result.output}"


def test_init_resume_flag_exits_zero():
    result = runner.invoke(app, ["init", "--resume", "./output-dir"])
    assert result.exit_code == 0


def test_init_unknown_flag_nonzero_exit():
    result = runner.invoke(app, ["init", "--unknown-flag"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# --profile real behavior tests (P02)
# ---------------------------------------------------------------------------

def _make_valid_profile():
    return {
        "name": "My Design System",
        "archetype": "enterprise-b2b",
        "colors": {
            "primary": "#1a73e8",
            "secondary": "#5f6368",
            "neutral": "#f1f3f4",
            "semantic": {
                "success": "#34a853",
                "warning": "#fbbc04",
                "error": "#ea4335",
                "info": "#4285f4",
            },
        },
        "typography": {"scaleRatio": 1.25, "baseSize": 16},
        "spacing": {"density": "compact"},
        "borderRadius": "sm",
        "elevation": "subtle",
        "motion": "reduced",
        "themes": ["light", "dark"],
        "accessibility": "AA",
        "componentScope": "comprehensive",
        "breakpoints": {"sm": "640px", "md": "768px", "lg": "1024px", "xl": "1280px"},
    }


def test_init_profile_valid_file_exits_zero(tmp_path):
    profile_path = tmp_path / "brand-profile.json"
    profile_path.write_text(json.dumps(_make_valid_profile()))

    result = runner.invoke(app, ["init", "--profile", str(profile_path)])
    assert result.exit_code == 0, f"Unexpected exit: {result.output}"
    assert "Profile loaded" in result.output or str(profile_path) in result.output


def test_init_profile_nonexistent_file_exits_one(tmp_path):
    missing = str(tmp_path / "missing.json")
    result = runner.invoke(app, ["init", "--profile", missing])
    assert result.exit_code == 1
    output = result.output.lower()
    assert "not found" in output or "does not exist" in output


def test_init_profile_invalid_archetype_exits_one(tmp_path):
    bad_profile = _make_valid_profile()
    bad_profile["archetype"] = "invalid-type"
    profile_path = tmp_path / "bad-profile.json"
    profile_path.write_text(json.dumps(bad_profile))

    result = runner.invoke(app, ["init", "--profile", str(profile_path)])
    assert result.exit_code == 1
    assert "archetype" in result.output


def test_init_profile_does_not_create_session_file(tmp_path, monkeypatch):
    profile_path = tmp_path / "brand-profile.json"
    profile_path.write_text(json.dumps(_make_valid_profile()))

    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--profile", str(profile_path)])

    assert not (tmp_path / ".daf-session.json").exists()


# ---------------------------------------------------------------------------
# p09: Resume and Gate 2 integration tests
# ---------------------------------------------------------------------------

def _make_valid_checkpoint_dir(output_dir) -> None:
    """Populate a valid Phase-3 checkpoint structure in output_dir."""
    from daf.tools.checkpoint_manager import CheckpointManager
    import json as _json
    from pathlib import Path as _Path

    od = _Path(output_dir)
    od.mkdir(parents=True, exist_ok=True)
    (od / "brand-profile.json").write_text(_json.dumps({"name": "Test"}))

    cm = CheckpointManager()
    cm.create(output_dir=str(od), phase=1)
    cm.create(output_dir=str(od), phase=2)
    cm.create(output_dir=str(od), phase=3)


def test_cli_resume_from_valid_checkpoint(tmp_path, monkeypatch):
    """--resume with valid phase-3 checkpoint starts first_publish_agent from phase 4."""
    _make_valid_checkpoint_dir(tmp_path)

    captured_start_phase = []

    def _mock_run_first_publish(output_dir, start_phase=1):
        captured_start_phase.append(start_phase)

    monkeypatch.setattr("daf.cli.run_first_publish_agent", _mock_run_first_publish)

    result = runner.invoke(app, ["init", "--resume", str(tmp_path)])
    assert result.exit_code == 0, f"Expected exit 0, got:\n{result.output}"
    assert captured_start_phase, "run_first_publish_agent was not called"
    assert captured_start_phase[0] == 4, (
        f"Expected start_phase=4 (resume after phase 3), got {captured_start_phase[0]}"
    )


def test_cli_resume_no_checkpoints_exits_nonzero(tmp_path):
    """--resume with no checkpoints exits with code 1 and reports the problem."""
    # tmp_path has no .daf-checkpoints directory at all
    result = runner.invoke(app, ["init", "--resume", str(tmp_path)])
    assert result.exit_code == 1
    assert "No valid checkpoints found" in result.output


def test_cli_gate2_approve_exits_zero(tmp_path, monkeypatch):
    """Gate 2 'A' (approve) input exits zero and confirms completion."""
    monkeypatch.chdir(tmp_path)

    # Mock out the full interview so it returns immediately
    monkeypatch.setattr("daf.interview.run_interview", lambda cwd: None)

    # Mock run_first_publish_agent to return a success result without LLM calls
    successful_result = {
        "pipeline": {"status": "success"},
        "phase_results": [],
    }
    monkeypatch.setattr("daf.cli.run_first_publish_agent", lambda od, **kw: successful_result)

    result = runner.invoke(app, ["init"], input="A\n")
    assert result.exit_code == 0, f"Expected exit 0, got:\n{result.output}"
    assert "Design system generation complete" in result.output
