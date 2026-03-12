import re


def test_import_daf():
    import daf

    assert daf.__version__
    assert re.match(r"\d+\.\d+\.\d+", daf.__version__)


def test_import_cli_app():
    from daf.cli import app

    assert callable(app)
