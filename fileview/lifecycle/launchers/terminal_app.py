"""macOS Terminal.app: one new window per viewer. Values reach AppleScript as `on run argv`
arguments, never spliced into script text, so no quoting can break the script."""
import shlex
import subprocess

LAUNCH = """
on run argv
    tell application "Terminal"
        set newTab to do script ("exec " & item 1 of argv)
        set custom title of newTab to item 2 of argv
        set title displays custom title of newTab to true
    end tell
end run
"""

CLOSE_IDLE = """
on run argv
    tell application "Terminal"
        close (every window whose name contains (item 1 of argv) and busy of selected tab is false)
    end tell
end run
"""


class TerminalApp:
    name = "Terminal.app"

    def launch(self, title: str, argv: list[str]) -> None:
        _osascript(LAUNCH, shlex.join(argv), title)

    def close_idle_windows(self, title_fragment: str) -> None:
        _osascript(CLOSE_IDLE, title_fragment)


def _osascript(script: str, *args: str) -> None:
    subprocess.run(["osascript", "-e", script, *args], capture_output=True, timeout=10)
