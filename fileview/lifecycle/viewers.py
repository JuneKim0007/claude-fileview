"""Open, close, signal and sweep viewer processes. The supervisor calls these under its lock; nothing
else opens viewers."""
import os
import subprocess
import sys
import time

from fileview.control.signals import SIGNAL_FOR_ACTION
from fileview.lifecycle import process_group, registry, windows
from fileview.lifecycle.launchers.detect import detect_launcher
from fileview.lifecycle.open_lock import open_lock
from fileview.locations import ENTRY_SCRIPT, STATE_DIR

CONFIRM_TRIES, CONFIRM_DELAY = 25, 0.2


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
        try:
            launcher.launch(windows.title_for(session), viewer_argv(session, config))
        except (subprocess.TimeoutExpired, OSError):     # e.g. a terminal still busy on first launch
            return f"{session}: {launcher.name} did not respond; nothing opened"
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
    windows.close_idle(windows.title_for(session), env)
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


def stop_all() -> tuple[int, int]:
    """Every viewer of this state directory, whatever its session; returns (stopped, found)."""
    groups = registry.all_viewer_groups()
    stopped = sum(process_group.terminate(group) for group in groups)
    registry.forget_all()
    return stopped, len(groups)
