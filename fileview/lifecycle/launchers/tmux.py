"""tmux: a detached horizontal split, titled; the pane closes when its process exits. Runs tmux with
the requesting session's environment, so the pane lands on that client's tmux server."""
import os
import shlex
import subprocess


class Tmux:
    name = "tmux"

    def __init__(self, env: dict[str, str] | None = None) -> None:
        self.env = {**os.environ, **(env or {})}

    def launch(self, title: str, argv: list[str]) -> None:
        split = subprocess.run(
            ["tmux", "split-window", "-h", "-d", "-l", "40%", "-P", "-F", "#{pane_id}", shlex.join(argv)],
            capture_output=True, text=True, timeout=10, env=self.env,
        )
        pane = split.stdout.strip()
        if pane:
            subprocess.run(["tmux", "select-pane", "-t", pane, "-T", title], capture_output=True, timeout=10, env=self.env)

    def close_idle_windows(self, title_fragment: str) -> None:
        pass
