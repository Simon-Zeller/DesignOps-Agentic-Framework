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
