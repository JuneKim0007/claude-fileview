"""Keep captures.json (what the hook extracts from command output) in step with the rules file the
default lookup resolves to. Checked at startup and on every reconcile pass; re-exported only when the
rules file changed. A malformed rules file exports the fallback rules' captures, the same rules the
viewers fall back to, so the hook and the windows never disagree."""
from fileview.config.captures_export import export
from fileview.config.load import load_rules
from fileview.config.lookup import choose
from fileview.control.file_watch import FileWatcher
from fileview.locations import DEFAULT_CONFIG


class CapturesSync:
    def __init__(self) -> None:
        self._watchers: list[FileWatcher] = []

    def refresh(self) -> str | None:
        """Re-export if needed; returns a log line when it did."""
        if self._watchers and not any(watcher.changed() for watcher in self._watchers):
            return None
        loaded = load_rules(None, confirm=None)
        self._watchers = [FileWatcher(str(choose().path)), FileWatcher(str(DEFAULT_CONFIG))]
        if export(loaded.rules.captures):
            return f"captures.json: {len(loaded.rules.captures)} capture(s) from {loaded.source}"
        return None
