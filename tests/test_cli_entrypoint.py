import subprocess
import sys
from pathlib import Path

# Use the daf binary from the same Python environment running the tests,
# so subprocess tests always target this project's installation.
_DAF_BIN = str(Path(sys.executable).parent / "daf")


def test_daf_help_exits_zero():
    result = subprocess.run(
        [_DAF_BIN, "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "init" in result.stdout


def test_daf_init_help_lists_flags():
    result = subprocess.run(
        [_DAF_BIN, "init", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--profile" in result.stdout
    assert "--resume" in result.stdout


def test_daf_no_args_no_traceback():
    result = subprocess.run(
        [_DAF_BIN],
        capture_output=True,
        text=True,
    )
    assert "Traceback" not in result.stderr
