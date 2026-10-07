"""The contract every terminal adapter implements."""
from typing import Protocol


class Launcher(Protocol):
    name: str

    def launch(self, title: str, argv: list[str]) -> None:
        """Start argv in a new window, tab or pane titled `title`."""

    def close_idle_windows(self, title_fragment: str) -> None:
        """Close windows whose title contains the fragment and that no longer run anything."""
