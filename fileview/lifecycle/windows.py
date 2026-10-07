"""Viewer windows as the user sees them: the title that names them, and closing the ones whose viewer
has exited (never one that still runs something)."""
import os
import time

from fileview.lifecycle.launchers.detect import detect_launcher

TITLE_PREFIX = "claude-fileview"
LEGACY_TITLE = "Claude files"          # windows opened by the bash version
SETTLE_SECONDS = 0.3                   # a window reports idle shortly after its process exits


def title_for(session: str) -> str:
    return f"{TITLE_PREFIX} {session}"


def close_idle(title_fragment: str, env: dict | None = None) -> None:
    launcher = detect_launcher(env if env is not None else os.environ)
    if launcher is not None:
        time.sleep(SETTLE_SECONDS)
        launcher.close_idle_windows(title_fragment)
