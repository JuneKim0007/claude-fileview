"""The repair pass (Kubernetes-controller style: compare intent with reality, fix the difference).
Runs every few seconds and once at startup:
  - a running viewer whose session is not wanted, or that holds no link past the grace period,
    is stopped (fail-closed: nothing runs unsupervised)
  - a wanted session whose Claude process ended is closed and forgotten
  - a wanted session with no viewer past the grace period is unwanted (window closed by hand, or crash)
  - at startup only: wanted sessions whose Claude is alive get their viewer reopened"""
import os
import time

from fileview.lifecycle import control, process_group, registry
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
    return "claude" in registry.process_args(pid)          # guards against a recycled pid


def reconcile(state: SupervisorState, now: float | None = None) -> list[str]:
    now = time.time() if now is None else now
    actions = []
    with state.lock:
        running = {session: group for group, session in registry.all_viewer_groups().items()}
        for session, group in running.items():
            entry = state.table.get(session)
            if session in state.attached:
                state.last_seen[session] = now
            elif not entry or not entry.wanted:
                if process_group.terminate(group):
                    registry.forget(session)
                    actions.append(f"stopped unmanaged viewer {session}")
            elif now - state.last_seen.get(session, 0) > GRACE_SECONDS:
                if process_group.terminate(group):
                    registry.forget(session)
                    actions.append(f"stopped unsupervised viewer {session} (no link)")
        for entry in state.table.all():
            if not entry.wanted:
                continue
            if entry.claude_pid and not claude_alive(entry.claude_pid):
                control.close_viewer(entry.session, entry.env)
                state.table.drop(entry.session)
                actions.append(f"closed {entry.session}: its Claude process ended")
            elif entry.session not in running and now - state.last_seen.get(entry.session, 0) > GRACE_SECONDS:
                state.table.unwant(entry.session)
                actions.append(f"{entry.session}: viewer gone (closed by hand or crashed); not reopening")
    return actions


def startup(state: SupervisorState) -> list[str]:
    """After a (re)start: clear what the previous supervisor left, reopen what is still wanted."""
    actions = [f"stopped leftover viewer {s}" for s in control.stop_unmanaged(set())]
    control.close_windows(control.TITLE_PREFIX)
    for entry in state.table.all():
        if not entry.wanted:
            continue
        if claude_alive(entry.claude_pid):
            state.mark_launching(entry.session)
            actions.append(control.open_viewer(entry.session, entry.config, entry.env))
        else:
            state.table.drop(entry.session)
    return actions
