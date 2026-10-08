"""Whether the Claude session behind this process is interactive. SDK, background and `claude -p`
sessions get no viewer window."""
import os

from fileview.lifecycle import processes


def is_interactive() -> bool:
    if os.environ.get("CLAUDE_CODE_SESSION_ATTENDED") == "0":
        return False
    claude_pid = os.environ.get("CLAUDE_PID")
    if not claude_pid:
        return True
    args = processes.args_of(claude_pid).split()
    if "-p" in args or "--print" in args:
        return False
    return processes.tty_of(claude_pid) not in ("", "??")
