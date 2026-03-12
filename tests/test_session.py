"""Tests for SessionManager (TDD red phase)."""

import json


def test_save_writes_session_file(tmp_path):
    from daf.session import SessionManager

    session = SessionManager(cwd=tmp_path)
    session.save(step=1, answers={"name": "TestDS"})

    session_file = tmp_path / ".daf-session.json"
    assert session_file.exists()


def test_save_writes_correct_content(tmp_path):
    from daf.session import SessionManager

    session = SessionManager(cwd=tmp_path)
    session.save(step=1, answers={"name": "TestDS"})

    data = json.loads((tmp_path / ".daf-session.json").read_text())
    assert data["last_step"] == 1
    assert data["answers"] == {"name": "TestDS"}


def test_load_returns_saved_state(tmp_path):
    from daf.session import SessionManager

    (tmp_path / ".daf-session.json").write_text(
        json.dumps({"last_step": 5, "answers": {"name": "TestDS", "archetype": "enterprise-b2b"}})
    )
    session = SessionManager(cwd=tmp_path)
    data = session.load()

    assert data is not None
    assert data["last_step"] == 5
    assert data["answers"]["name"] == "TestDS"


def test_load_returns_none_when_no_file(tmp_path):
    from daf.session import SessionManager

    session = SessionManager(cwd=tmp_path)
    assert session.load() is None


def test_delete_removes_session_file(tmp_path):
    from daf.session import SessionManager

    session_file = tmp_path / ".daf-session.json"
    session_file.write_text(json.dumps({"last_step": 3, "answers": {}}))

    session = SessionManager(cwd=tmp_path)
    session.delete()

    assert not session_file.exists()


def test_save_is_idempotent(tmp_path):
    from daf.session import SessionManager

    session = SessionManager(cwd=tmp_path)
    session.save(step=3, answers={"name": "First"})
    session.save(step=3, answers={"name": "Updated"})

    data = json.loads((tmp_path / ".daf-session.json").read_text())
    assert data["answers"]["name"] == "Updated"
    assert data["last_step"] == 3


def test_session_uses_cwd_by_default(monkeypatch, tmp_path):
    from daf.session import SessionManager

    monkeypatch.chdir(tmp_path)
    session = SessionManager()
    session.save(step=1, answers={"name": "TestDS"})

    assert (tmp_path / ".daf-session.json").exists()


def test_delete_is_noop_when_no_file(tmp_path):
    from daf.session import SessionManager

    session = SessionManager(cwd=tmp_path)
    # Should not raise
    session.delete()
