"""Whether the rules file a viewer loaded has changed since it was read (mtime and size), so the
viewer can queue a reload. Polled from the viewer's idle tick; no threads."""
import os


class FileWatcher:
    def __init__(self, path: str) -> None:
        self.path = path
        self._stamp = self._read_stamp()

    def changed(self) -> bool:
        stamp = self._read_stamp()
        if stamp == self._stamp:
            return False
        self._stamp = stamp
        return True

    def _read_stamp(self) -> tuple[float, int] | None:
        try:
            stat = os.stat(self.path)
        except OSError:
            return None
        return stat.st_mtime, stat.st_size
