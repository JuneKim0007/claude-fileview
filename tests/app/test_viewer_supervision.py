"""The viewer loop's supervision behaviour (fail-closed exit, handover, re-exec), driven through
viewer.run with the log, the rules and the supervisor link replaced by fakes."""
import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from fileview.app import viewer
from fileview.config.load import LoadedRules
from fileview.rules.defaults import DEFAULT_RULES
from fileview.supervisor.client import SupervisorUnavailable
from fileview.supervisor.link import CLOSED, HANDOVER, UP, ViewerOutdated


class FakeLink:
    def __init__(self, *states):
        self.states = list(states)

    def state(self):
        return self.states.pop(0) if len(self.states) > 1 else self.states[0]


def idle_log(_path):
    while True:
        yield None


class Supervision(unittest.TestCase):
    def run_viewer(self, first, reattach=None):
        patches = [
            mock.patch.object(viewer.SupervisorLink, "attach", return_value=first),
            mock.patch.object(viewer.SupervisorLink, "reattach", side_effect=reattach or (lambda *_: FakeLink(CLOSED))),
            mock.patch.object(viewer, "follow", idle_log),
            mock.patch.object(viewer, "load_rules", return_value=LoadedRules(DEFAULT_RULES, "built-in defaults")),
            mock.patch.object(viewer, "session_title", return_value=None),
            mock.patch.object(viewer.signals, "install"),
            mock.patch.object(viewer, "_reexec_for_new_code", return_value=42),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        out = io.StringIO()
        with redirect_stdout(out):
            code = viewer.run("s1")
        return code, out.getvalue()

    def test_a_closed_link_exits_zero(self):
        code, out = self.run_viewer(FakeLink(UP, UP, CLOSED))
        self.assertEqual(code, 0)
        self.assertIn("fileview: supervisor gone; exiting", out)

    def test_handover_reattaches_and_keeps_running(self):
        second = FakeLink(UP, CLOSED)
        code, out = self.run_viewer(FakeLink(UP, HANDOVER), reattach=lambda *_: second)
        self.assertEqual(code, 0)
        self.assertIn("fileview: supervisor upgrading; reattaching", out)
        self.assertIn("fileview: supervisor gone; exiting", out)       # it ran on, on the new link

    def test_handover_with_no_successor_exits_zero(self):
        def nobody(*_):
            raise SupervisorUnavailable("timed out")
        code, out = self.run_viewer(FakeLink(HANDOVER), reattach=nobody)
        self.assertEqual(code, 0)
        self.assertIn("fileview: no supervisor took over (timed out); exiting", out)

    def test_handover_to_newer_code_re_execs(self):
        def newer(*_):
            raise ViewerOutdated("newer")
        code, _ = self.run_viewer(FakeLink(HANDOVER), reattach=newer)
        self.assertEqual(code, 42)


if __name__ == "__main__":
    unittest.main()
