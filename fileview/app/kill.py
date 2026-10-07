"""`fileview kill`: stop everything without needing the supervisor to answer. Supervisor first, so it
cannot reopen anything; then every viewer, their records, and their windows."""
from fileview.lifecycle import viewers, windows
from fileview.supervisor.stopper import stop_supervisor


def kill_all() -> str:
    supervisor = stop_supervisor()
    stopped, found = viewers.stop_all()
    windows.close_idle(windows.TITLE_PREFIX)
    windows.close_idle(windows.LEGACY_TITLE)
    return f"supervisor {supervisor}; stopped {stopped} of {found} viewer(s); closed idle viewer windows"
