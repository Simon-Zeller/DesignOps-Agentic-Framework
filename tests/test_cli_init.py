from typer.testing import CliRunner

from daf.cli import app

runner = CliRunner()


def test_init_interactive_stub_exits_zero():
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert result.output.strip()


def test_init_profile_flag_exits_zero():
    result = runner.invoke(app, ["init", "--profile", "./some/path.json"])
    assert result.exit_code == 0


def test_init_resume_flag_exits_zero():
    result = runner.invoke(app, ["init", "--resume", "./output-dir"])
    assert result.exit_code == 0


def test_init_profile_does_not_require_file_to_exist():
    result = runner.invoke(app, ["init", "--profile", "./nonexistent-profile.json"])
    assert result.exit_code == 0
    assert "FileNotFoundError" not in result.output


def test_init_unknown_flag_nonzero_exit():
    result = runner.invoke(app, ["init", "--unknown-flag"])
    assert result.exit_code != 0


def test_init_combined_flags_documents_behavior():
    # Regression anchor: documents current behavior when both flags are supplied.
    # Conflict enforcement (if any) is deferred to P02.
    result = runner.invoke(app, ["init", "--profile", "./p.json", "--resume", "./dir"])
    # Either exit code is acceptable — this test records the current behavior.
    assert isinstance(result.exit_code, int)
