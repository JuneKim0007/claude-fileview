"""One opener per session at a time (the SessionStart hook and a manual open can race).
mkdir is atomic, so the directory is the lock; one older than STALE_SECONDS is left from a crash."""
import time
from contextlib import contextmanager
from typing import Iterator

from fileview.locations import VIEWERS_DIR

STALE_SECONDS = 30


@contextmanager
def open_lock(session: str) -> Iterator[bool]:
    VIEWERS_DIR.mkdir(parents=True, exist_ok=True)
    lock = VIEWERS_DIR / f"{session}.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        if time.time() - lock.stat().st_mtime < STALE_SECONDS:
            yield False
            return
    try:
        yield True
    finally:
        lock.rmdir()
