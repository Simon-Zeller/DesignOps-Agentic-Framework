"""Session persistence manager for the DAF brand interview.

Saves, loads, and deletes `.daf-session.json` so interrupted interviews
can be resumed.  All path logic is relative to the *cwd* passed at
construction time — no hard-coded `Path.cwd()` calls outside the
constructor.
"""

import json
from pathlib import Path
from typing import Any

_SESSION_FILENAME = ".daf-session.json"


class SessionManager:
    """Manages a `.daf-session.json` file in a given working directory."""

    def __init__(self, cwd: Path | None = None) -> None:
        self._cwd = Path(cwd) if cwd is not None else Path.cwd()

    @property
    def _path(self) -> Path:
        return self._cwd / _SESSION_FILENAME

    def save(self, step: int, answers: dict[str, object]) -> None:
        """Persist the current interview state to disk."""
        payload = {"last_step": step, "answers": answers}
        self._path.write_text(json.dumps(payload, indent=2))

    def load(self) -> dict[str, Any] | None:
        """Load the saved session state, or return None if no file exists."""
        if not self._path.exists():
            return None
        result: dict[str, Any] = json.loads(self._path.read_text())
        return result

    def delete(self) -> None:
        """Remove the session file if it exists."""
        if self._path.exists():
            self._path.unlink()
