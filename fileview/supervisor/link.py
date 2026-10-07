"""A viewer's link to the supervisor. The viewer refuses to start without one, and exits as soon as
the supervisor's end closes (the kernel closes it if the supervisor dies), so no viewer outlives
supervision. The link is two-way, so the supervisor can later push actions down it."""
import os
import socket

from fileview.locations import SUPERVISOR_SOCKET
from fileview.supervisor import protocol
from fileview.supervisor.client import SupervisorUnavailable


class SupervisorLink:
    def __init__(self, connection: socket.socket) -> None:
        self._connection = connection

    @classmethod
    def attach(cls, session: str) -> "SupervisorLink":
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            connection.settimeout(5)
            connection.connect(str(SUPERVISOR_SOCKET))
            connection.sendall(protocol.encode({"op": "attach", "session": session, "pid": os.getpid(),
                                                "version": protocol.code_version()}))
            reply = protocol.decode(connection.makefile("rb").readline())
        except (OSError, ValueError) as failure:
            connection.close()
            raise SupervisorUnavailable(f"cannot reach the supervisor: {failure}") from None
        if not reply.get("ok"):
            connection.close()
            raise SupervisorUnavailable(f"supervisor refused the link: {reply.get('error')}")
        connection.setblocking(False)
        return cls(connection)

    def alive(self) -> bool:
        try:
            return self._connection.recv(1, socket.MSG_PEEK) != b""
        except BlockingIOError:
            return True                         # nothing to read, still connected
        except OSError:
            return False
