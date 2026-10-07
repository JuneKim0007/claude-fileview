"""Read-only questions about running processes, answered by ps: one process's command line, the
command lines in a process group, every (group, command line) on the machine."""
import subprocess


def args_of(pid: int) -> str:
    lines = _ps("-o", "args=", "-p", str(pid))
    return lines[0].strip() if lines else ""


def args_in_group(group: int) -> list[str]:
    return [line.strip() for line in _ps("-o", "args=", "-g", str(group))]


def all_groups_and_args() -> list[tuple[int, str]]:
    found = []
    for line in _ps("-axo", "pgid=,args="):
        group, _, args = line.strip().partition(" ")
        if group.isdigit():
            found.append((int(group), args.strip()))
    return found


def _ps(*args: str) -> list[str]:
    return subprocess.run(["ps", *args], capture_output=True, text=True).stdout.splitlines()
