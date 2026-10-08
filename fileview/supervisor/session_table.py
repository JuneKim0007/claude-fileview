"""The sessions the supervisor manages, persisted so a restarted supervisor can rebuild its intent.
`wanted` is the user's intent: set by open/ensure, cleared by close, kill, a hand-closed window, or
the Claude process ending. Only wanted sessions are reopened after a supervisor restart."""
import json
import os
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path

from fileview.locations import SUPERVISOR_STATE


@dataclass
class Session:
    session: str
    claude_pid: int = 0                      # 0: unknown (opened by hand outside Claude)
    config: str | None = None
    env: dict[str, str] = field(default_factory=dict)    # terminal hints: TERM_PROGRAM, TMUX
    wanted: bool = True


class SessionTable:
    def __init__(self, path: Path = SUPERVISOR_STATE) -> None:
        self.path = path
        self._lock = threading.RLock()
        self._sessions: dict[str, Session] = {}

    def load(self) -> "SessionTable":
        try:
            data = json.loads(self.path.read_text())
            self._sessions = {item["session"]: Session(**item) for item in data}
        except (FileNotFoundError, ValueError, TypeError, KeyError):
            self._sessions = {}
        return self

    def get(self, session: str) -> Session | None:
        with self._lock:
            return self._sessions.get(session)

    def env_of(self, session: str) -> dict[str, str] | None:
        entry = self.get(session)
        return entry.env if entry else None

    def put(self, entry: Session) -> None:
        with self._lock:
            self._sessions[entry.session] = entry
            self._save()

    def unwant(self, session: str) -> None:
        with self._lock:
            if session in self._sessions:
                self._sessions[session].wanted = False
                self._save()

    def unwant_all(self) -> int:
        with self._lock:
            wanted = [entry for entry in self._sessions.values() if entry.wanted]
            for entry in wanted:
                entry.wanted = False
            if wanted:
                self._save()
            return len(wanted)

    def drop(self, session: str) -> None:
        with self._lock:
            if self._sessions.pop(session, None) is not None:
                self._save()

    def all(self) -> list[Session]:
        with self._lock:
            return list(self._sessions.values())

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        partial = self.path.with_name(self.path.name + ".partial")
        partial.write_text(json.dumps([asdict(s) for s in self._sessions.values()], indent=1))
        os.replace(partial, self.path)
