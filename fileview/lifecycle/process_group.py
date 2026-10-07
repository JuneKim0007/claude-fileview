"""The only code that sends signals: stop a viewer's process group, or send one signal to one viewer
process. Refuses this process's own group and pid, so a wrong record can never take Claude down."""
import os
import signal
import time

PROTECTED_GROUPS = (0, 1)
WAIT_TRIES, WAIT_DELAY = 10, 0.1


def send(pid: int, signum: int) -> bool:
    """Deliver one signal to one process; False if it is protected or already gone."""
    if pid in PROTECTED_GROUPS or pid == os.getpid():
        return False
    try:
        os.kill(pid, signum)
    except ProcessLookupError:
        return False
    return True


def terminate(group: int) -> bool:
    """SIGTERM the group; True once it is gone (or already was)."""
    if group in PROTECTED_GROUPS or group == os.getpgrp():
        return False
    try:
        os.killpg(group, signal.SIGTERM)
    except ProcessLookupError:
        return True
    for _ in range(WAIT_TRIES):
        if not alive(group):
            return True
        time.sleep(WAIT_DELAY)
    return not alive(group)


def alive(group: int) -> bool:
    try:
        os.killpg(group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
