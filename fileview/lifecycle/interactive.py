"""Whether the Claude session behind this process is interactive. SDK, background and `claude -p`
sessions get no viewer window."""
import os
import subprocess


def is_interactive() -> bool:
    if os.environ.get("CLAUDE_CODE_SESSION_ATTENDED") == "0":
        return False
    claude_pid = os.environ.get("CLAUDE_PID")
    if not claude_pid:
        return True
    args = _ps(claude_pid, "args=").split()
    if "-p" in args or "--print" in args:
        return False
    return _ps(claude_pid, "tty=") not in ("", "??")


def _ps(pid: str, field: str) -> str:
    return subprocess.run(["ps", "-o", field, "-p", pid], capture_output=True, text=True).stdout.strip()
