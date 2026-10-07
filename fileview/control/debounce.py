"""Collapse a burst of triggers into one: due() is true once, after no poke() for `quiet` seconds.
A window drag sends a stream of SIGWINCH; the viewer redraws only when the size has settled."""
import time


class Debounce:
    def __init__(self, quiet: float) -> None:
        self.quiet = quiet
        self._last_poke: float | None = None

    def poke(self, now: float | None = None) -> None:
        self._last_poke = time.monotonic() if now is None else now

    def due(self, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        if self._last_poke is None or now - self._last_poke < self.quiet:
            return False
        self._last_poke = None
        return True
