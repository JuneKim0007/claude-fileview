"""Talk to the supervisor: connect, start it if nothing answers, replace it if it runs older code.
Fail-closed: when it cannot be reached or started, SupervisorUnavailable is raised and the caller
opens nothing."""
import socket
import subprocess
import sys
import time

from fileview.locations import ENTRY_SCRIPT, HOME, SUPERVISOR_LOG, SUPERVISOR_SOCKET
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
        return protocol.decode(connection.makefile("rb").readline())


def _start_and_wait() -> None:
    if holder_pid() is None:
        SUPERVISOR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(SUPERVISOR_LOG, "a") as log:
            subprocess.Popen(
                [sys.executable, "-E", "-s", str(ENTRY_SCRIPT), "supervisor", "run"],
                stdin=subprocess.DEVNULL, stdout=log, stderr=log, cwd=HOME,
                start_new_session=True,       # its own session: survives the Claude session that started it
            )
    deadline = time.time() + READY_SECONDS
    while time.time() < deadline:
        try:
            if request({"op": "ping", "version": protocol.code_version()}, 1).get("ok"):
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.1)
    raise SupervisorUnavailable(f"supervisor did not start within {READY_SECONDS}s; see {SUPERVISOR_LOG}")


def _replace() -> None:
    """The running supervisor has older code: stop it (its viewers exit with it) and start ours.
    The new one reopens the viewers its sessions still want."""
    from fileview.lifecycle.control import stop_supervisor
    stop_supervisor()
    if holder_pid() is not None:
        raise SupervisorUnavailable("old supervisor did not stop; run: fileview kill")
    _start_and_wait()
