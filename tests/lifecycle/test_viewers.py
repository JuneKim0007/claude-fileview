import subprocess
import unittest
from contextlib import contextmanager
from unittest import mock

from fileview.lifecycle import viewers


@contextmanager
def acquired(_session):
    yield True


class SlowTerminal:
    name = "SlowTerm"

    def launch(self, title, argv):
        raise subprocess.TimeoutExpired("osascript", 10)

    def close_idle_windows(self, title_fragment):
        raise subprocess.TimeoutExpired("osascript", 10)


class TerminalThatDoesNotAnswer(unittest.TestCase):
    def setUp(self):
        for owner, target, value in ((viewers, "open_lock", acquired),
                                     (viewers, "detect_launcher", lambda _env: SlowTerminal()),
                                     (viewers.windows, "detect_launcher", lambda _env: SlowTerminal()),
                                     (viewers.windows.time, "sleep", lambda _seconds: None)):
            patch = mock.patch.object(owner, target, value)
            patch.start()
            self.addCleanup(patch.stop)
        live = mock.patch.object(viewers.registry, "live_group", return_value=None)
        live.start()
        self.addCleanup(live.stop)

    def test_open_reports_the_timeout_instead_of_raising(self):
        message = viewers.open_viewer("s1", None, {"TERM_PROGRAM": "iTerm.app"})
        self.assertEqual(message, "s1: SlowTerm did not respond; nothing opened")

    def test_closing_windows_survives_the_timeout(self):
        viewers.windows.close_idle("claude-fileview", {"TERM_PROGRAM": "iTerm.app"})


if __name__ == "__main__":
    unittest.main()
