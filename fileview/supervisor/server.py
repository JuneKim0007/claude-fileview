"""The supervisor process: single instance, a Unix socket for requests and viewer links, a reconcile
thread. Stays up until `fileview supervisor stop` or `fileview kill`, which end every viewer with it
(fail-closed), or until a "handover" request (a newer supervisor is taking over), which tells each
viewer to keep its window and reattach instead."""
import logging
import os
import signal
import socket
import socketserver
import threading
import time

from fileview.lifecycle import registry, windows
from fileview.locations import SUPERVISOR_SOCKET
from fileview.supervisor import handlers, protocol, reconcile
from fileview.supervisor.captures_sync import CapturesSync
from fileview.supervisor.session_table import SessionTable
from fileview.supervisor.singleton import Singleton
from fileview.supervisor.state import SupervisorState

log = logging.getLogger("fileview.supervisor")
VERSIONLESS_OPS = ("ping", "shutdown", "handover")   # what a client with other code may still ask


class _Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    state: SupervisorState


class _Connection(socketserver.StreamRequestHandler):
    server: _Server

    def handle(self) -> None:
        state = self.server.state
        try:
            message = protocol.decode(self.rfile.readline())
        except ValueError:
            self.wfile.write(protocol.encode(protocol.error("bad_message")))
            return
        if message.get("version") != state.version and message["op"] not in VERSIONLESS_OPS:
            self.wfile.write(protocol.encode(protocol.error("version_mismatch", supervisor=state.version)))
            return
        if message["op"] == "attach":
            self._hold_link(state, (message.get("session") or "")[:8])
            return
        response = handlers.dispatch(state, message, self.server.shutdown)
        log.info("%s %s -> %s", message.get("op"), message.get("session", ""), response.get("message", response))
        self.wfile.write(protocol.encode(response))

    def _hold_link(self, state: SupervisorState, session: str) -> None:
        state.attach(session, self.connection)
        self.wfile.write(protocol.encode(protocol.ok(attached=session)))
        log.info("attached %s", session)
        while self.rfile.readline():          # blocks until the viewer's end of the link closes
            pass
        state.detach(session, self.connection)
        log.info("detached %s", session)


def serve() -> int:
    logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
    singleton = Singleton()
    if not singleton.acquire():
        log.info("another supervisor holds the lock; exiting")
        return 1
    os.umask(0o077)                            # socket and state files: this user only
    SUPERVISOR_SOCKET.parent.mkdir(parents=True, exist_ok=True)
    SUPERVISOR_SOCKET.unlink(missing_ok=True)  # safe: holding the lock means any socket file is stale
    state = SupervisorState(table=SessionTable().load())
    server = _Server(str(SUPERVISOR_SOCKET), _Connection)
    server.state = state

    def stop(*_args) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    log.info("supervisor %s up (pid %s)", state.version, os.getpid())
    for action in reconcile.startup(state):
        log.info("startup: %s", action)
    captures = CapturesSync()
    _refresh_captures(captures)
    threading.Thread(target=_reconcile_loop, args=(state, captures), daemon=True).start()
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        state.stopping.set()
        server.server_close()
        SUPERVISOR_SOCKET.unlink(missing_ok=True)
        handing_over = state.handing_over.is_set()
        for connection in list(state.attached.values()):
            if handing_over:
                _send_handover(connection)     # viewers keep their windows and reattach
            _end_link(connection)              # otherwise viewers see the link close and exit
        if not handing_over:
            _wait_for_viewers_to_exit()        # a window only reads as idle once its viewer is gone
            windows.close_idle(windows.TITLE_PREFIX)
        log.info("supervisor %s", "handed over" if handing_over else "down")
    return 0


def _send_handover(connection: socket.socket) -> None:
    try:
        connection.sendall(protocol.encode({"op": "handover"}))
    except OSError:
        pass


def _end_link(connection: socket.socket) -> None:
    """shutdown() sends FIN now and wakes the thread blocked reading this link; close() alone would
    not while that read is in progress, and the viewer would never learn the supervisor is gone."""
    try:
        connection.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    connection.close()


def _wait_for_viewers_to_exit(seconds: float = 3.0) -> None:
    deadline = time.time() + seconds
    while registry.all_viewer_groups() and time.time() < deadline:
        time.sleep(0.1)


def _reconcile_loop(state: SupervisorState, captures: CapturesSync) -> None:
    while not state.stopping.wait(reconcile.INTERVAL_SECONDS):
        try:
            for action in reconcile.reconcile(state):
                log.info("reconcile: %s", action)
        except Exception:                      # noqa: BLE001 - one bad pass must not end supervision
            log.exception("reconcile failed")
        _refresh_captures(captures)


def _refresh_captures(captures: CapturesSync) -> None:
    try:
        note = captures.refresh()
        if note:
            log.info(note)
    except Exception:                          # noqa: BLE001 - capture sync must not end supervision
        log.exception("captures sync failed")
