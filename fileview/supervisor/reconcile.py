"""The repair pass (Kubernetes-controller style: compare intent with reality, fix the difference).
Runs every few seconds and once at startup:
  - a running viewer whose session is not wanted, or that holds no link past the grace period,
    is stopped (fail-closed: nothing runs unsupervised)
  - a wanted session whose Claude process ended is closed and forgotten
  - a wanted session with no viewer past the grace period is unwanted (window closed by hand, or crash)
  - at startup only: wanted sessions whose Claude is alive get their viewer reopened"""
import os
import time

from fileview.lifecycle import process_group, processes, registry, viewers, windows
from fileview.supervisor.state import SupervisorState

INTERVAL_SECONDS = 5
GRACE_SECONDS = 10          # a launching or re-exec'ing viewer gets this long to (re)attach


def claude_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    return "claude" in processes.args_of(pid)          # guards against a recycled pid


def reconcile(state: SupervisorState, now: float | None = None) -> list[str]:
    now = time.time() if now is None else now
    with state.lock:
        running = {session: group for group, session in registry.all_viewer_groups().items()}
        return _sweep_running(state, running, now) + _review_wanted(state, running, now)


def _sweep_running(state: SupervisorState, running: dict[str, int], now: float) -> list[str]:
    actions = []
    for session, group in running.items():
        if state.is_attached(session):
            state.seen(session, now)
            continue
        reason = _why_stop(state, session, now)
        if reason and _stop(session, group):
            actions.append(reason)
    return actions


def _why_stop(state: SupervisorState, session: str, now: float) -> str | None:
    entry = state.table.get(session)
    if not entry or not entry.wanted:
        return f"stopped unmanaged viewer {session}"
    if state.stale(session, now, GRACE_SECONDS):
        return f"stopped unsupervised viewer {session} (no link)"
    return None


def _review_wanted(state: SupervisorState, running: dict[str, int], now: float) -> list[str]:
    actions = []
    for entry in state.table.all():
        if not entry.wanted:
            continue
        if entry.claude_pid and not claude_alive(entry.claude_pid):
            viewers.close_viewer(entry.session, entry.env)
            state.table.drop(entry.session)
            actions.append(f"closed {entry.session}: its Claude process ended")
        elif entry.session not in running and state.stale(entry.session, now, GRACE_SECONDS):
            state.table.unwant(entry.session)
            actions.append(f"{entry.session}: viewer gone (closed by hand or crashed); not reopening")
    return actions


def _stop(session: str, group: int) -> bool:
    if not process_group.terminate(group):
        return False
    registry.forget(session)
    return True


def startup(state: SupervisorState) -> list[str]:
    """After a (re)start: stop viewers nobody wants; give viewers of wanted sessions that are still
    running (handing over from the previous supervisor) the grace period to reattach; reopen only
    wanted sessions that have no viewer at all."""
    wanted = {entry.session for entry in state.table.all() if entry.wanted and claude_alive(entry.claude_pid)}
    actions = [f"stopped leftover viewer {s}" for s in viewers.stop_unmanaged(wanted)]
    windows.close_idle(windows.TITLE_PREFIX)
    for entry in state.table.all():
        if entry.session not in wanted:
            if entry.wanted:
                state.table.drop(entry.session)            # its Claude process is gone
            continue
        state.mark_launching(entry.session)
        if registry.live_group(entry.session):
            actions.append(f"{entry.session}: viewer still running; waiting for it to reattach")
        else:
            actions.append(viewers.open_viewer(entry.session, entry.config, entry.env))
    return actions
