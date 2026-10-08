"""A viewer's link to the supervisor. The viewer refuses to start without one. When the link closes
the viewer exits (fail-closed), unless the supervisor first sent "handover": a planned upgrade, like
nginx's binary upgrade, where the viewer keeps its window and reattaches to the new supervisor."""
import os
import socket
import time

from fileview.locations import SUPERVISOR_SOCKET
from fileview.supervisor import protocol
from fileview.supervisor.client import SupervisorUnavailable

UP, HANDOVER, CLOSED = "up", "handover", "closed"
RETRY_SECONDS = 0.2


class ViewerOutdated(SupervisorUnavailable):
    """The supervisor runs newer code than this viewer: re-exec the viewer to load it."""


class SupervisorLink:
    def __init__(self, connection: socket.socket) -> None:
        self._connection = connection
        self._buffer = b""
        self._handover = False

    @classmethod
    def attach(cls, session: str) -> "SupervisorLink":
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            connection.settimeout(5)
            connection.connect(str(SUPERVISOR_SOCKET))
            connection.sendall(protocol.encode({"op": "attach", "session": session, "pid": os.getpid(),
                                                "version": protocol.code_version()}))
            reply = protocol.decode_response(connection.makefile("rb").readline())
        except (OSError, ValueError) as failure:
            connection.close()
            raise SupervisorUnavailable(f"cannot reach the supervisor: {failure}") from None
        if not reply.get("ok"):
            connection.close()
            if reply.get("error") == "version_mismatch":
                raise ViewerOutdated(f"supervisor runs {reply.get('supervisor')}, viewer {protocol.code_version()}")
            raise SupervisorUnavailable(f"supervisor refused the link: {reply.get('error')}")
        connection.setblocking(False)
        return cls(connection)

    @classmethod
    def reattach(cls, session: str, within: float) -> "SupervisorLink":
        """Attach to the supervisor that replaces the one that handed over; ViewerOutdated passes through."""
        deadline = time.monotonic() + within
        while True:
            try:
                return cls.attach(session)
            except ViewerOutdated:
                raise
            except SupervisorUnavailable:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(RETRY_SECONDS)

    def state(self) -> str:
        """UP, HANDOVER (planned: reattach), or CLOSED (failure: exit). Never blocks."""
        while True:
            try:
                data = self._connection.recv(4096)
            except BlockingIOError:
                return HANDOVER if self._handover else UP
            except OSError:
                data = b""
            if not data:
                self._connection.close()
                return HANDOVER if self._handover else CLOSED
            self._buffer += data
            *lines, self._buffer = self._buffer.split(b"\n")
            for line in lines:
                try:
                    if protocol.decode_request(line)["op"] == "handover":
                        self._handover = True
                except ValueError:
                    pass
