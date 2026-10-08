"""The confirmation port: ask a yes/no question before anything is overwritten. Returns True, False,
or None when nobody can be asked. The terminal implementation is here; an MCP one can be passed
anywhere a Confirm is accepted."""
import sys


def terminal_confirm(question: str) -> bool | None:
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return None
    try:
        answer = input(f"{question} [y/N] ")
    except EOFError:
        return None
    return answer.strip().lower() in ("y", "yes")
