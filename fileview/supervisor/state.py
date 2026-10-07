"""The supervisor's in-memory state: the persisted session table, which viewers hold a live link, and
when each wanted session last had a running viewer. Memory is a cache over the table and the process
list, so a restarted supervisor rebuilds it in one reconcile pass (crash-only design)."""
import socket
import threading
import time
from dataclasses import dataclass, field

from fileview.supervisor.protocol import code_version
from fileview.supervisor.session_table import SessionTable


@dataclass
class SupervisorState:
    table: SessionTable
    lock: threading.RLock = field(default_factory=threading.RLock)    # serialises every lifecycle action
    attached: dict[str, socket.socket] = field(default_factory=dict)  # session -> viewer link
    last_seen: dict[str, float] = field(default_factory=dict)         # session -> last time a viewer was up
    started: float = field(default_factory=time.time)
    version: str = field(default_factory=code_version)
    stopping: threading.Event = field(default_factory=threading.Event)

    def attach(self, session: str, connection: socket.socket) -> None:
        with self.lock:
            self.attached[session] = connection
            self.last_seen[session] = time.time()

    def detach(self, session: str, connection: socket.socket) -> None:
        with self.lock:
            if self.attached.get(session) is connection:       # a newer link (in-place restart) wins
                del self.attached[session]
                self.last_seen[session] = time.time()

    def mark_launching(self, session: str) -> None:
        with self.lock:
            self.last_seen[session] = time.time()              # start the grace period for a new viewer
