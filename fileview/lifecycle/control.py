"""The actions on viewer windows and processes. The supervisor calls these under its lock; nothing
else opens viewers. kill_all is the exception by design: it works with no supervisor at all, so a
dead or wedged supervisor can always be cleared away together with every viewer."""
import os
import signal
import sys
import time

from fileview.control.signals import SIGNAL_FOR_ACTION
from fileview.lifecycle import process_group, registry
from fileview.lifecycle.launchers.detect import detect_launcher
from fileview.lifecycle.open_lock import open_lock
from fileview.locations import ENTRY_SCRIPT, STATE_DIR, SUPERVISOR_SOCKET, VIEWERS_DIR

TITLE_PREFIX = "claude-fileview"
LEGACY_TITLE = "Claude files"          # windows opened by the bash version
CONFIRM_TRIES, CONFIRM_DELAY = 25, 0.2
WINDOW_SETTLE_SECONDS = 0.3            # a window reports idle shortly after its process exits
SUPERVISOR_ARGS = f"{ENTRY_SCRIPT} supervisor run"


def title_for(session: str) -> str:
    return f"{TITLE_PREFIX} {session}"


def viewer_argv(session: str, config: str | None) -> list[str]:
    argv = [sys.executable, "-E", "-s", str(ENTRY_SCRIPT), "view", session]
    if config:
        argv += ["--config", config]
    return argv + ["--state", str(STATE_DIR)]            # scopes the viewer to this supervisor's state


def open_viewer(session: str, config: str | None = None, env: dict | None = None) -> str:
    with open_lock(session) as acquired:
        if not acquired:
            return f"{session}: open already in progress"
        if registry.live_group(session):
            return f"{session}: already open"
        launcher = detect_launcher(env if env is not None else os.environ)
        if launcher is None:
            return f"{session}: no supported terminal (TERM_PROGRAM/TMUX not recognised)"
        launcher.launch(title_for(session), viewer_argv(session, config))
        for _ in range(CONFIRM_TRIES):
            if registry.live_group(session):
                return f"{session}: opened ({launcher.name})"
            time.sleep(CONFIRM_DELAY)
        return f"{session}: launch sent, viewer not confirmed (macOS automation permission?)"


def close_viewer(session: str, env: dict | None = None) -> str:
    group = registry.live_group(session)
    if group is None:
        return f"{session}: not open"
    process_group.terminate(group)
    registry.forget(session)
    close_windows(title_for(session), env)
    return f"{session}: closed"


def signal_viewer(session: str, action: str) -> str:
    pid = registry.live_pid(session)
    if pid is None or not process_group.send(pid, SIGNAL_FOR_ACTION[action]):
        return f"{session}: not open"
    return f"{session}: {action} requested"


def stop_unmanaged(managed: set[str]) -> list[str]:
    """Stop every running viewer whose session is not in `managed` (fail-closed: nothing unsupervised)."""
    stopped = []
    for group, session in registry.all_viewer_groups().items():
        if session not in managed and process_group.terminate(group):
            registry.forget(session)
            stopped.append(session)
    return stopped


def kill_all() -> str:
    """Supervisor first (so it cannot reopen anything), then every viewer, records and windows."""
    supervisor = stop_supervisor()
    groups = registry.all_viewer_groups()
    stopped = sum(process_group.terminate(group) for group in groups)
    for record in VIEWERS_DIR.glob("*.pgid"):
        record.unlink(missing_ok=True)
    close_windows(TITLE_PREFIX)
    close_windows(LEGACY_TITLE)
    return f"supervisor {supervisor}; stopped {stopped} of {len(groups)} viewer(s); closed idle viewer windows"


def close_windows(title_fragment: str, env: dict | None = None) -> None:
    launcher = detect_launcher(env if env is not None else os.environ)
    if launcher is not None:
        time.sleep(WINDOW_SETTLE_SECONDS)
        launcher.close_idle_windows(title_fragment)


def stop_supervisor() -> str:
    """Stop the supervisor without talking to it: the lock names its pid, the command line proves it."""
    from fileview.supervisor.singleton import holder_pid
    pid = holder_pid()
    if pid is None:
        SUPERVISOR_SOCKET.unlink(missing_ok=True)
        return "not running"
    args = registry.process_args(pid)
    if SUPERVISOR_ARGS not in args:                 # the lock names a pid that is not our supervisor
        return f"lock names pid {pid}, which is not a supervisor ({args or 'gone'}); left alone"
    process_group.send(pid, signal.SIGTERM)
    for _ in range(60):                             # its shutdown waits for viewers, then closes windows
        if holder_pid() is None:
            break
        time.sleep(0.1)
    else:
        process_group.send(pid, signal.SIGKILL)     # wedged: the kernel releases its lock on exit
        time.sleep(0.2)
    SUPERVISOR_SOCKET.unlink(missing_ok=True)
    return f"stopped (pid {pid})"
