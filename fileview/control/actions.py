"""Named actions a running viewer can perform, and the queue triggers feed. Triggers (signal handlers,
the config watcher, later an MCP or command channel) only enqueue names; the viewer loop drains the
queue between lines, so actions never run inside a signal handler."""
from collections import deque
from typing import Callable, Generic, TypeVar

Target = TypeVar("Target")


class ActionRegistry(Generic[Target]):
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[Target], None]] = {}
        self._pending: deque[str] = deque()

    def register(self, name: str, handler: Callable[[Target], None]) -> None:
        self._handlers[name] = handler

    def names(self) -> list[str]:
        return sorted(self._handlers)

    def request(self, name: str) -> None:
        """Safe to call from a signal handler: appending to a deque is atomic."""
        self._pending.append(name)

    def run_pending(self, target: Target) -> list[str]:
        ran = []
        while self._pending:
            name = self._pending.popleft()
            handler = self._handlers.get(name)
            if handler is not None and name not in ran:     # a burst of the same request runs once
                handler(target)
                ran.append(name)
        return ran
