"""Follow the log like `tail -F`: yield recent lines, then new ones as they arrive; reopen after
rotation (inode changes) or truncation (size shrinks). Yields None on each idle tick so the caller
can do periodic work without threads."""
import os
import time
from collections import deque
from pathlib import Path
from typing import Iterator

IDLE_SECONDS = 0.2


def follow(path: Path, backfill: int = 2000) -> Iterator[str | None]:
    handle, inode, first_open = None, None, True
    try:
        while True:
            if handle is None:
                try:
                    handle = open(path, "rb")    # binary: byte offsets are needed to rewind partial lines
                    inode = os.fstat(handle.fileno()).st_ino
                except FileNotFoundError:
                    yield None
                    time.sleep(IDLE_SECONDS)
                    continue
                if first_open:
                    recent = deque(handle, maxlen=backfill)
                    if recent and not recent[-1].endswith(b"\n"):     # a writer is mid-line: re-read later
                        handle.seek(-len(recent.pop()), os.SEEK_CUR)
                    for raw in recent:
                        yield _decode(raw)
                    first_open = False
            raw = handle.readline()
            if raw.endswith(b"\n"):
                yield _decode(raw)
                continue
            if raw:                                       # a writer is mid-line: wait for the rest
                handle.seek(-len(raw), os.SEEK_CUR)
            yield None
            time.sleep(IDLE_SECONDS)
            if _replaced(path, inode, handle.tell()):
                handle.close()
                handle = None
    finally:                                              # runs when the caller closes the generator
        if handle is not None:
            handle.close()


def _decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


def _replaced(path: Path, inode: int, position: int) -> bool:
    try:
        stat = os.stat(path)
    except FileNotFoundError:
        return True
    return stat.st_ino != inode or stat.st_size < position
