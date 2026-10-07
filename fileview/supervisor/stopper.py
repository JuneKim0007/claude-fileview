"""Stop the supervisor without talking to it: the lock names its pid, its command line proves it is
ours. Used by `fileview supervisor stop`, `fileview kill`, and the client when replacing old code."""
import signal
import time

from fileview.lifecycle import process_group, processes
from fileview.locations import ENTRY_SCRIPT, SUPERVISOR_SOCKET
from fileview.supervisor.singleton import holder_pid

SUPERVISOR_ARGS = f"{ENTRY_SCRIPT} supervisor run"
GRACEFUL_SECONDS = 6.0                 # its shutdown waits for viewers, then closes windows


def stop_supervisor() -> str:
    pid = holder_pid()
    if pid is None:
        SUPERVISOR_SOCKET.unlink(missing_ok=True)
        return "not running"
    args = processes.args_of(pid)
    if SUPERVISOR_ARGS not in args:                 # the lock names a pid that is not our supervisor
        return f"lock names pid {pid}, which is not a supervisor ({args or 'gone'}); left alone"
    process_group.send(pid, signal.SIGTERM)
    deadline = time.time() + GRACEFUL_SECONDS
    while holder_pid() is not None and time.time() < deadline:
        time.sleep(0.1)
    if holder_pid() is not None:
        process_group.send(pid, signal.SIGKILL)     # wedged: the kernel releases its lock on exit
        time.sleep(0.2)
    SUPERVISOR_SOCKET.unlink(missing_ok=True)
    return f"stopped (pid {pid})"
