"""At most one supervisor per user, enforced by an flock the kernel releases the instant the holder
dies, so a crashed supervisor can never leave a lock that looks held. The holder's pid is written
into the lock file for diagnostics and for `fileview kill`."""
import fcntl
import os
from pathlib import Path

from fileview.locations import SUPERVISOR_LOCK


class Singleton:
    def __init__(self, path: Path = SUPERVISOR_LOCK) -> None:
        self.path = path
        self._handle = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self.path, "a+")
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            return False
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()))
        handle.flush()
        self._handle = handle          # held for the life of the process
        return True


def holder_pid(path: Path = SUPERVISOR_LOCK) -> int | None:
    """The live supervisor's pid, or None when nobody holds the lock."""
    if not path.exists():
        return None
    with open(path, "a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.seek(0)
            text = handle.read().strip()
            return int(text) if text.isdigit() else None
        fcntl.flock(handle, fcntl.LOCK_UN)
        return None
