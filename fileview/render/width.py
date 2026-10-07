"""Terminal width now. Resizes arrive as the "redraw" action (SIGWINCH, see control/signals.py)."""
import shutil

FALLBACK_COLUMNS = 100


def columns() -> int:
    return shutil.get_terminal_size((FALLBACK_COLUMNS, 24)).columns
