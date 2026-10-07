"""One request -> one response. Every lifecycle action runs under the supervisor lock, so two
sessions (or a hook and a manual command) can never interleave opens and closes."""
import os
import threading
import time

from fileview.lifecycle import registry, viewers
from fileview.supervisor import protocol
from fileview.supervisor.session_table import Session
from fileview.supervisor.state import SupervisorState


def dispatch(state: SupervisorState, message: dict, shutdown) -> dict:
    op, session = message.get("op"), (message.get("session") or "")[:8]
    if op == "ping":
        return protocol.ok(pid=os.getpid(), version=state.version, uptime=round(time.time() - state.started))
    if op == "list":
        return protocol.ok(sessions=_listing(state))
    if op == "shutdown":
        threading.Thread(target=shutdown, daemon=True).start()
        return protocol.ok(message="supervisor stopping")
    if op == "handover":
        state.handing_over.set()
        threading.Thread(target=shutdown, daemon=True).start()
        return protocol.ok(message="supervisor handing over")
    if not session:
        return protocol.error("missing_session")
    with state.lock:
        if op in ("ensure", "open"):
            return protocol.ok(message=_open(state, session, message))
        if op == "close":
            state.table.unwant(session)
            entry = state.table.get(session)
            return protocol.ok(message=viewers.close_viewer(session, entry.env if entry else None))
        if op == "reload":
            return protocol.ok(message=viewers.signal_viewer(session, "reload"))
        if op == "restart":
            if message.get("config"):                       # a new rules file needs a fresh window
                entry = state.table.get(session)
                viewers.close_viewer(session, entry.env if entry else None)
                return protocol.ok(message=_open(state, session, message))
            if registry.live_pid(session):
                return protocol.ok(message=viewers.signal_viewer(session, "restart"))
            return protocol.ok(message=_open(state, session, message))
        if op == "status":
            entry = state.table.get(session)
            return protocol.ok(session=session, open=registry.live_group(session) is not None,
                               attached=session in state.attached, wanted=bool(entry and entry.wanted))
    return protocol.error("unknown_op", op=op)


def _open(state: SupervisorState, session: str, message: dict) -> str:
    previous = state.table.get(session)
    entry = Session(
        session=session,
        claude_pid=int(message.get("claude_pid") or (previous.claude_pid if previous else 0)),
        config=message.get("config") or (previous.config if previous else None),
        env=message.get("env") or (previous.env if previous else {}),
        wanted=True,
    )
    state.table.put(entry)
    state.mark_launching(session)
    return viewers.open_viewer(session, entry.config, entry.env)


def _listing(state: SupervisorState) -> list[dict]:
    running = {session: group for group, session in registry.all_viewer_groups().items()}
    return [{"session": e.session, "wanted": e.wanted, "open": e.session in running,
             "attached": e.session in state.attached, "claude_pid": e.claude_pid} for e in state.table.all()]
