"""Size-based rotation: past the limit, the log moves to <name>.1 (replacing the previous one).
Called with the writer's lock held; followers notice the new inode and reopen."""
import os
from pathlib import Path

MAX_BYTES = 5 * 1024 * 1024


def rotate_if_large(log: Path, max_bytes: int = MAX_BYTES) -> None:
    try:
        if log.stat().st_size > max_bytes:
            os.replace(log, log.with_name(log.name + ".1"))
    except FileNotFoundError:
        pass
