"""Pick the terminal adapter from the environment of the session that asked (not the supervisor's
own environment: one supervisor serves sessions in different terminals)."""
import os

from fileview.lifecycle.launchers.base import Launcher
from fileview.lifecycle.launchers.iterm import ITerm
from fileview.lifecycle.launchers.terminal_app import TerminalApp
from fileview.lifecycle.launchers.tmux import Tmux

TERMINAL_HINTS = ("TERM_PROGRAM", "TMUX")


def terminal_hints(env=os.environ) -> dict[str, str]:
    return {key: env[key] for key in TERMINAL_HINTS if env.get(key)}


def detect_launcher(env=os.environ) -> Launcher | None:
    if env.get("TMUX"):
        return Tmux(dict(env))
    program = env.get("TERM_PROGRAM", "")
    if program == "iTerm.app":
        return ITerm()
    if program == "Apple_Terminal":
        return TerminalApp()
    return None
