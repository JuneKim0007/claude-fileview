"""One request -> one response. Every lifecycle action runs under the supervisor lock, so two
sessions (or a hook and a manual command) can never interleave opens and closes."""
import os
import threading
import time

from fileview.lifecycle import registry, viewers
from fileview.locations import CODE_ROOT
from fileview.supervisor import protocol
from fileview.supervisor.session_table import Session
from fileview.supervisor.state import SupervisorState


def dispatch(state: SupervisorState, message: dict, shutdown) -> dict:
    op, session = message.get("op"), protocol.session_key(message.get("session"))
    if op in SUPERVISOR_OPS:
        return SUPERVISOR_OPS[op](state, shutdown)
    if not session:
        return protocol.error("missing_session")
    handler = SESSION_OPS.get(op)
    if handler is None:
        return protocol.error("unknown_op", op=op)
    with state.lock:
        return handler(state, session, message)


def _ping(state: SupervisorState, _shutdown) -> dict:
    return protocol.ok(pid=os.getpid(), version=state.version, uptime=round(time.time() - state.started),
                       root=str(CODE_ROOT))


def _list(state: SupervisorState, _shutdown) -> dict:
    return protocol.ok(sessions=_listing(state))


def _shutdown(_state: SupervisorState, shutdown) -> dict:
    threading.Thread(target=shutdown, daemon=True).start()
    return protocol.ok(message="supervisor stopping")


def _handover(state: SupervisorState, shutdown) -> dict:
    state.handing_over.set()
    threading.Thread(target=shutdown, daemon=True).start()
    return protocol.ok(message="supervisor handing over")


def _ensure(state: SupervisorState, session: str, message: dict) -> dict:
    return protocol.ok(message=_open(state, session, message))


def _close(state: SupervisorState, session: str, _message: dict) -> dict:
    state.table.unwant(session)
    return protocol.ok(message=viewers.close_viewer(session, state.table.env_of(session)))


def _reload(_state: SupervisorState, session: str, _message: dict) -> dict:
    return protocol.ok(message=viewers.signal_viewer(session, "reload"))


def _restart(state: SupervisorState, session: str, message: dict) -> dict:
    if message.get("config"):                       # a new rules file needs a fresh window
        viewers.close_viewer(session, state.table.env_of(session))
        return protocol.ok(message=_open(state, session, message))
    if registry.live_pid(session):
        return protocol.ok(message=viewers.signal_viewer(session, "restart"))
    return protocol.ok(message=_open(state, session, message))


def _status(state: SupervisorState, session: str, _message: dict) -> dict:
    entry = state.table.get(session)
    return protocol.ok(session=session, open=registry.live_group(session) is not None,
                       attached=state.is_attached(session), wanted=bool(entry and entry.wanted))


SUPERVISOR_OPS = {"ping": _ping, "list": _list, "shutdown": _shutdown, "handover": _handover}
SESSION_OPS = {"ensure": _ensure, "open": _ensure, "close": _close, "reload": _reload,
               "restart": _restart, "status": _status}


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
             "attached": state.is_attached(e.session), "claude_pid": e.claude_pid} for e in state.table.all()]
