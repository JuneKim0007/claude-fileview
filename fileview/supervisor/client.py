"""Talk to the supervisor: connect, start it if nothing answers, replace it if it runs older code.
Fail-closed: when it cannot be reached or started, SupervisorUnavailable is raised and the caller
opens nothing."""
import socket
import subprocess
import sys
import time

from fileview.locations import CODE_ROOT, ENTRY_SCRIPT, HOME, SUPERVISOR_LOG, SUPERVISOR_SOCKET
from fileview.supervisor import protocol
from fileview.supervisor.singleton import holder_pid

READY_SECONDS = 5


class SupervisorUnavailable(Exception):
    pass


def call(op: str, timeout: float = 20, start: bool = True, **fields) -> dict:
    message = {"op": op, "version": protocol.code_version(), **fields}
    try:
        response = request(message, timeout)
    except OSError:
        if not start:
            raise SupervisorUnavailable("supervisor is not running") from None
        _start_and_wait()
        response = request(message, timeout)
    if response.get("error") == "version_mismatch":
        if not start:
            raise SupervisorUnavailable(f"supervisor runs other code ({response.get('supervisor')})")
        _replace()
        response = request(message, timeout)
    return response


def request(message: dict, timeout: float) -> dict:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(timeout)
        connection.connect(str(SUPERVISOR_SOCKET))
        connection.sendall(protocol.encode(message))
        line = connection.makefile("rb").readline()
    if not line:                     # accepted, then closed unanswered: that supervisor is going away
        raise ConnectionError("supervisor closed the connection without answering")
    return protocol.decode_response(line)


def _start_and_wait() -> None:
    """Start a supervisor once the lock is free (a previous one may still be finishing its exit), then
    wait until it answers. Several clients may race here; the lock lets exactly one of their spawns run."""
    started = False
    deadline = time.time() + READY_SECONDS
    while time.time() < deadline:
        if not started and holder_pid() is None:
            _spawn()
            started = True
        try:
            if request({"op": "ping", "version": protocol.code_version()}, 1).get("ok"):
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.1)
    raise SupervisorUnavailable(f"supervisor did not start within {READY_SECONDS}s; see {SUPERVISOR_LOG}")


def _refuse_other_install() -> None:
    try:
        root = request({"op": "ping", "version": "any"}, 2).get("root")
    except (OSError, ValueError):
        return                                   # not answering: nothing running to take over from
    if root is not None and root != str(CODE_ROOT):   # no root: a supervisor from before roots were reported
        raise SupervisorUnavailable(
            f"the running supervisor belongs to {root}, not this copy ({CODE_ROOT}). Run this copy with its "
            f"own CLAUDE_FILEVIEW_STATE, or stop the other first: fileview supervisor stop")


def _spawn() -> None:
    SUPERVISOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SUPERVISOR_LOG, "a") as log:
        subprocess.Popen(
            [sys.executable, "-E", "-s", str(ENTRY_SCRIPT), "supervisor", "run"],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log, cwd=HOME,
            start_new_session=True,           # its own session: survives the Claude session that started it
        )


def _replace() -> None:
    """The running supervisor has other code: ask it to hand over (its viewers keep their windows and
    reattach to ours), then start ours. A supervisor too old to hand over is stopped instead. Only an
    upgrade of the same install may replace it: a different copy sharing this state directory is refused."""
    from fileview.supervisor.stopper import stop_supervisor
    _refuse_other_install()
    try:
        handed_over = request({"op": "handover", "version": "any"}, 5).get("ok", False)
    except (OSError, ValueError):
        handed_over = False
    deadline = time.time() + READY_SECONDS
    while handed_over and holder_pid() is not None and time.time() < deadline:
        time.sleep(0.05)
    if holder_pid() is not None:
        stop_supervisor()
    if holder_pid() is not None:
        raise SupervisorUnavailable("old supervisor did not stop; run: fileview kill")
    _start_and_wait()
