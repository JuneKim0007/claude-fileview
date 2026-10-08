"""iTerm2: a vertical split of the current session, or a new window when iTerm2 has no current window
(none open, or none focused). iTerm closes the pane when its process exits."""
import shlex
import subprocess

LAUNCH = """
on run argv
    tell application "iTerm"
        try
            tell current session of current window
                set viewer to (split vertically with default profile command (item 1 of argv))
            end tell
        on error
            set viewer to current session of (create window with default profile command (item 1 of argv))
        end try
        set name of viewer to item 2 of argv
    end tell
end run
"""


class ITerm:
    name = "iTerm2"

    def launch(self, title: str, argv: list[str]) -> None:
        subprocess.run(["osascript", "-e", LAUNCH, shlex.join(argv), title], capture_output=True, timeout=10)

    def close_idle_windows(self, title_fragment: str) -> None:
        pass
