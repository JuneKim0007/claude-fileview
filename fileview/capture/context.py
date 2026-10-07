"""The fields every event from one hook payload shares, and the factory that stamps them."""
import time
from dataclasses import dataclass

from fileview.capture.project_root import project_root
from fileview.model.event import Event
from fileview.model.kind import Kind


@dataclass(frozen=True)
class HookContext:
    session: str
    agent: str
    cwd: str
    root: str
    ts: float

    @classmethod
    def from_payload(cls, payload: dict) -> "HookContext":
        cwd = payload.get("cwd") or ""
        return cls(
            session=payload.get("session_id") or "-",
            agent=payload.get("agent_type") or "main",
            cwd=cwd,
            root=project_root(cwd),
            ts=time.time(),
        )

    def event(self, kind: Kind, path: str = "", detail: str = "", values: dict | None = None) -> Event:
        return Event(self.ts, self.session, self.agent, kind, path, detail, self.root, values or {})
