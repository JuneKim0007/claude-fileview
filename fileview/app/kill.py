"""`fileview kill`: stop everything without needing the supervisor to answer. Supervisor first, so it
cannot reopen anything; then no session is wanted any more, so the next supervisor reopens nothing;
then every viewer, their records, and their windows."""
from fileview.lifecycle import viewers, windows
from fileview.supervisor.session_table import SessionTable
from fileview.supervisor.stopper import stop_supervisor


def kill_all() -> str:
    supervisor = stop_supervisor()
    released = SessionTable().load().unwant_all()
    stopped, found = viewers.stop_all()
    windows.close_idle(windows.TITLE_PREFIX)
    windows.close_idle(windows.LEGACY_TITLE)
    return (f"supervisor {supervisor}; {released} session(s) no longer wanted; "
            f"stopped {stopped} of {found} viewer(s); closed idle viewer windows")
