"""Every supervisor operation through handlers.dispatch, with viewer processes replaced by fakes."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fileview.supervisor import handlers, protocol
from fileview.supervisor.session_table import Session, SessionTable
from fileview.supervisor.state import SupervisorState

ENV = {"TERM_PROGRAM": "Apple_Terminal"}


class Operations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = SupervisorState(table=SessionTable(Path(self.tmp.name) / "t.json"))
        self.calls = []
        fakes = {
            "open_viewer": lambda s, config, env: self.calls.append(("open", s, config, env)) or f"{s}: opened",
            "close_viewer": lambda s, env: self.calls.append(("close", s, env)) or f"{s}: closed",
            "signal_viewer": lambda s, action: self.calls.append(("signal", s, action)) or f"{s}: {action} requested",
        }
        for name, fake in fakes.items():
            patch = mock.patch.object(handlers.viewers, name, side_effect=fake)
            patch.start()
            self.addCleanup(patch.stop)
        self.live_pid = mock.patch.object(handlers.registry, "live_pid", return_value=None)
        self.live_pid.start()
        self.addCleanup(self.live_pid.stop)
        group = mock.patch.object(handlers.registry, "live_group", return_value=None)
        group.start()
        self.addCleanup(group.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def send(self, op, **fields):
        return handlers.dispatch(self.state, {"op": op, **fields}, shutdown=lambda: None)

    def test_ensure_records_the_session_and_opens(self):
        reply = self.send("ensure", session="abcdef1234", claude_pid=7, env=ENV)
        self.assertEqual(reply, protocol.ok(message="abcdef12: opened"))
        self.assertEqual(self.calls, [("open", "abcdef12", None, ENV)])
        entry = self.state.table.get("abcdef12")
        self.assertEqual((entry.claude_pid, entry.env, entry.wanted), (7, ENV, True))

    def test_open_keeps_what_an_earlier_ensure_recorded(self):
        self.send("ensure", session="s1", claude_pid=7, env=ENV, config="/c.yaml")
        self.calls.clear()
        self.send("open", session="s1")
        self.assertEqual(self.calls, [("open", "s1", "/c.yaml", ENV)])
        self.assertEqual(self.state.table.get("s1").claude_pid, 7)

    def test_close_unwants_and_closes_with_the_recorded_env(self):
        self.state.table.put(Session("s1", env=ENV))
        reply = self.send("close", session="s1")
        self.assertEqual(reply, protocol.ok(message="s1: closed"))
        self.assertEqual(self.calls, [("close", "s1", ENV)])
        self.assertFalse(self.state.table.get("s1").wanted)

    def test_reload_signals(self):
        self.assertEqual(self.send("reload", session="s1"), protocol.ok(message="s1: reload requested"))
        self.assertEqual(self.calls, [("signal", "s1", "reload")])

    def test_restart_with_a_new_config_closes_then_reopens(self):
        self.state.table.put(Session("s1", env=ENV))
        self.send("restart", session="s1", config="/new.yaml")
        self.assertEqual(self.calls, [("close", "s1", ENV), ("open", "s1", "/new.yaml", ENV)])

    def test_restart_of_a_running_viewer_signals_it(self):
        self.live_pid.stop()
        with mock.patch.object(handlers.registry, "live_pid", return_value=123):
            self.send("restart", session="s1")
        self.live_pid.start()
        self.assertEqual(self.calls, [("signal", "s1", "restart")])

    def test_restart_without_a_viewer_opens_one(self):
        self.send("restart", session="s1")
        self.assertEqual(self.calls, [("open", "s1", None, {})])

    def test_status(self):
        self.state.table.put(Session("s1"))
        self.assertEqual(self.send("status", session="s1"),
                         protocol.ok(session="s1", open=False, attached=False, wanted=True))

    def test_session_operations_need_a_session(self):
        for op in ("ensure", "open", "close", "reload", "restart", "status"):
            self.assertEqual(self.send(op), protocol.error("missing_session"))

    def test_unknown_operation(self):
        self.assertEqual(self.send("nope", session="s1"), protocol.error("unknown_op", op="nope"))

    def test_handover_sets_the_flag(self):
        self.assertEqual(self.send("handover"), protocol.ok(message="supervisor handing over"))
        self.assertTrue(self.state.handing_over.is_set())


if __name__ == "__main__":
    unittest.main()
