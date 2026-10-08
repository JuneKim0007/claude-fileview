"""Composition root of a viewer process: load rules, install triggers, follow the log, render one
session's events, and run requested actions (reload, restart, redraw) between lines.

Triggers -> action names -> handlers here. Signals and the rules-file watcher are the triggers today;
anything else that can enqueue a name (a command channel, an MCP tool) plugs into the same registry."""
import os
import sys

from fileview.config.load import LoadedRules, load_rules
from fileview.control import signals
from fileview.control.actions import ActionRegistry
from fileview.control.confirm import terminal_confirm
from fileview.control.debounce import Debounce
from fileview.control.file_watch import FileWatcher
from fileview.locations import LOG_FILE
from fileview.model.event import Event
from fileview.render.header import header, title_banner
from fileview.render.line import format_event
from fileview.render.palette import Palette
from fileview.render.width import columns
from fileview.store.follower import follow
from fileview.supervisor.client import SupervisorUnavailable
from fileview.supervisor.link import CLOSED, HANDOVER, SupervisorLink, ViewerOutdated
from fileview.transcript.session_title import session_title

POLL_TICKS = 10              # idle ticks of 0.2 s between title / rules-file checks
RESIZE_QUIET_SECONDS = 0.5   # redraw the banner once the window size has been stable this long
HANDOVER_SECONDS = 5.0       # a planned upgrade must hand over within this, or the viewer exits
REEXEC_ENV, MAX_REEXECS = "CLAUDE_FILEVIEW_REEXECS", 3


class Viewer:
    def __init__(self, session: str, config: str | None) -> None:
        self.session, self.config = session, config
        self.loaded: LoadedRules = load_rules(config, confirm=terminal_confirm)   # may ask at startup only
        self.palette = Palette.for_stream(sys.stdout, self.loaded.rules.palette)
        self.watcher = self._watch()
        self.title = session_title(session)
        self.shown_root = ""
        self.banner_width = 0
        self.resized = Debounce(RESIZE_QUIET_SECONDS)

    def reload(self) -> None:
        """Re-read rules without asking anything; on failure keep the last good rules and say why."""
        fresh = load_rules(self.config, confirm=None)
        if fresh.problems:
            fresh.rules, fresh.source = self.loaded.rules, f"{self.loaded.source} (kept; new version rejected)"
        self.loaded = fresh
        self.palette = Palette.for_stream(sys.stdout, fresh.rules.palette)
        self.watcher = self._watch()
        self.redraw()

    def restart(self) -> None:
        sys.stdout.flush()
        os.execv(sys.executable, [sys.executable, *sys.orig_argv[1:]])

    def redraw(self) -> None:
        problems = [str(problem) for problem in self.loaded.problems]
        self.banner_width = columns()
        _emit(header(self.title, self.session, self.banner_width, self.palette, self.loaded.source,
                     problems, self.loaded.notes))

    def resize(self) -> None:
        self.resized.poke()                         # many per drag; settle() acts once it stops

    def settle(self) -> None:
        if self.resized.due() and columns() != self.banner_width:
            self.banner_width = columns()
            _emit(title_banner(self.title, self.session, self.banner_width, self.palette))

    def show(self, event: Event) -> None:
        if event.root and event.root != self.shown_root:
            self.shown_root = event.root
            _emit(self.palette.dim("root " + _home_short(event.root)))
        for line in format_event(event, self.shown_root, columns(), self.palette, self.loaded.rules):
            _emit(line)

    def poll(self) -> None:
        latest = session_title(self.session)
        if latest != self.title:
            self.title = latest
            self.redraw()

    def _watch(self) -> FileWatcher | None:
        return FileWatcher(self.loaded.source) if os.path.isfile(self.loaded.source) else None


def run(session: str, config: str | None = None) -> int:
    try:
        link = SupervisorLink.attach(session)          # fail-closed: no supervisor, no viewer
    except ViewerOutdated:
        return _reexec_for_new_code()
    except SupervisorUnavailable as failure:
        _emit(f"fileview: not starting: {failure}")
        return 1
    os.environ.pop(REEXEC_ENV, None)                   # attached: the re-exec cap counts consecutive tries only
    actions: ActionRegistry[Viewer] = ActionRegistry()
    actions.register("reload", Viewer.reload)
    actions.register("restart", Viewer.restart)
    actions.register("redraw", Viewer.redraw)
    actions.register("resize", Viewer.resize)
    signals.install(actions)

    if sys.stdout.isatty():
        sys.stdout.write(f"\033]0;claude-fileview {session}\007")
    viewer = Viewer(session, config)
    viewer.redraw()
    ticks = 0
    for raw in follow(LOG_FILE):
        actions.run_pending(viewer)
        viewer.settle()
        if raw is None:
            ticks += 1
            link_state = link.state()
            if link_state == CLOSED:                   # a failure, not a planned upgrade
                _emit("fileview: supervisor gone; exiting")
                return 0
            if link_state == HANDOVER:
                _emit(viewer.palette.dim("fileview: supervisor upgrading; reattaching"))
                try:
                    link = SupervisorLink.reattach(session, HANDOVER_SECONDS)
                except ViewerOutdated:
                    return _reexec_for_new_code()
                except SupervisorUnavailable as failure:
                    _emit(f"fileview: no supervisor took over ({failure}); exiting")
                    return 0
            if ticks % POLL_TICKS == 0:
                viewer.poll()
                if viewer.watcher and viewer.watcher.changed():
                    actions.request("reload")
            continue
        event = Event.from_json(raw)
        if event is not None and event.session.startswith(session):
            viewer.show(event)
    return 0


def _reexec_for_new_code() -> int:
    """The supervisor runs newer code: replace this process with itself (same pid, same window) so it
    loads that code. Capped, so code that keeps changing cannot make it loop."""
    count = int(os.environ.get(REEXEC_ENV, "0"))
    if count >= MAX_REEXECS:
        _emit("fileview: viewer code keeps changing under it; exiting")
        return 1
    os.environ[REEXEC_ENV] = str(count + 1)
    sys.stdout.flush()
    os.execv(sys.executable, [sys.executable, *sys.orig_argv[1:]])
    return 1                                           # unreachable: execv does not return


def _home_short(path: str) -> str:
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path == home or path.startswith(home + os.sep) else path


def _emit(text: str) -> None:
    try:
        print(text, flush=True)
    except BrokenPipeError:
        raise SystemExit(0)
