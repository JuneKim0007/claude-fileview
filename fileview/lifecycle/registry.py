"""Which viewer belongs to which session. A viewer records "<pgid> <pid>" in viewers/<sid>.pgid;
a record counts only while that group still runs a viewer process for the same session, so stale
records and recycled pids are never trusted (or signalled). The group is for stopping the whole
window's processes; the pid is for action signals, which must reach the viewer and nothing else."""
import os
import re

from fileview.lifecycle import processes
from fileview.locations import CLAUDE_HOME, ENTRY_SCRIPT, STATE_DIR, VIEWERS_DIR

_DEFAULT_STATE = str(CLAUDE_HOME / "fileview-state")    # viewers started without --state belong here

# the bash viewer this replaced; later bash versions ran it under `exec -a "claude-fileview <sid>"`
LEGACY_VIEWER = re.compile(r"^(?:/bin/bash|claude-fileview \S+) \S*/touched-view\.sh (\S+)$")


def viewer_session(args: str) -> str | None:
    """The session a process command line is a viewer for, or None. Matches the interpreter plus the
    exact argument tail, so a shell whose command line merely mentions a viewer never qualifies."""
    program, _, rest = args.partition(" ")
    tail = f"{ENTRY_SCRIPT} view "
    if "ython" in os.path.basename(program) and rest.startswith("-E -s " + tail):
        words = rest[len("-E -s " + tail):].split()          # "<session> [--config PATH] [--state DIR]"
        state = words[words.index("--state") + 1] if "--state" in words[:-1] else _DEFAULT_STATE
        return words[0] if words and state == str(STATE_DIR) else None   # another state dir's viewer is not ours
    legacy = LEGACY_VIEWER.match(args)
    return legacy.group(1) if legacy and str(STATE_DIR) == _DEFAULT_STATE else None


def record(session: str) -> None:
    VIEWERS_DIR.mkdir(parents=True, exist_ok=True)
    (VIEWERS_DIR / f"{session}.pgid").write_text(f"{os.getpgrp()} {os.getpid()}")


def forget(session: str) -> None:
    (VIEWERS_DIR / f"{session}.pgid").unlink(missing_ok=True)


def forget_all() -> None:
    for record_file in VIEWERS_DIR.glob("*.pgid"):
        record_file.unlink(missing_ok=True)


def live_group(session: str) -> int | None:
    ids = _recorded_ids(session)
    if ids and any(viewer_session(args) == session for args in processes.args_in_group(ids[0])):
        return ids[0]
    if ids is not None:          # a record whose group no longer runs this viewer is stale
        forget(session)
    return None


def live_pid(session: str) -> int | None:
    """The viewer process itself, verified by its command line."""
    ids = _recorded_ids(session)
    if not ids or len(ids) < 2:
        return None
    return ids[1] if viewer_session(processes.args_of(ids[1])) == session else None


def all_viewer_groups() -> dict[int, str]:
    """Every running viewer's process group -> session, found by scanning processes, not records."""
    found = {}
    for group, args in processes.all_groups_and_args():
        session = viewer_session(args)
        if session:
            found[group] = session
    return found


def recorded_sessions() -> list[str]:
    return sorted(p.stem for p in VIEWERS_DIR.glob("*.pgid")) if VIEWERS_DIR.exists() else []


def _recorded_ids(session: str) -> list[int] | None:
    try:
        return [int(part) for part in (VIEWERS_DIR / f"{session}.pgid").read_text().split()]
    except (FileNotFoundError, ValueError):
        return None
