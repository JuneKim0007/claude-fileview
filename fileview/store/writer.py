"""Append events to the log, one JSON line each, under an exclusive lock so concurrent hooks never
interleave partial lines."""
import fcntl

from fileview.locations import LOG_FILE
from fileview.model.event import Event
from fileview.store.rotation import rotate_if_large


def append(events: list[Event]) -> None:
    if not events:
        return
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        fcntl.flock(log, fcntl.LOCK_EX)
        try:
            log.write("".join(event.to_json() + "\n" for event in events))
            log.flush()
            rotate_if_large(LOG_FILE)
        finally:
            fcntl.flock(log, fcntl.LOCK_UN)
