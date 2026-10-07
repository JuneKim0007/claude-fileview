import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fileview.supervisor import protocol, reconcile
from fileview.supervisor.session_table import Session, SessionTable
from fileview.supervisor.singleton import Singleton, holder_pid
from fileview.supervisor.state import SupervisorState


class Protocol(unittest.TestCase):
    def test_round_trip_and_version_is_stable(self):
        message = {"op": "ensure", "session": "abc", "version": protocol.code_version()}
        self.assertEqual(protocol.decode(protocol.encode(message)), message)
        self.assertEqual(protocol.code_version(), protocol.code_version())

    def test_rejects_non_messages(self):
        for line in (b"[1, 2]\n", b'{"x": 1}\n', b"nope\n"):
            with self.assertRaises(ValueError):
                protocol.decode(line)


class Singletons(unittest.TestCase):
    def test_second_acquire_fails_and_holder_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "s.lock"
            self.assertIsNone(holder_pid(lock))
            first = Singleton(lock)
            self.assertTrue(first.acquire())
            self.assertEqual(holder_pid(lock), os.getpid())
            self.assertFalse(Singleton(lock).acquire())    # flock is per open file: a second handle is refused
            first._handle.close()                          # what the kernel does when the holder dies
            self.assertIsNone(holder_pid(lock))


class Table(unittest.TestCase):
    def test_persists_and_reloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sessions.json"
            table = SessionTable(path)
            table.put(Session("s1", claude_pid=42, env={"TERM_PROGRAM": "Apple_Terminal"}))
            table.put(Session("s2"))
            table.unwant("s2")
            reloaded = SessionTable(path).load()
            self.assertEqual(reloaded.get("s1").claude_pid, 42)
            self.assertFalse(reloaded.get("s2").wanted)

    def test_corrupt_file_starts_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sessions.json"
            path.write_text("{not json")
            self.assertEqual(SessionTable(path).load().all(), [])


class Reconcile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = SupervisorState(table=SessionTable(Path(self.tmp.name) / "t.json"))
        self.terminated = []
        patches = [
            mock.patch("fileview.supervisor.reconcile.process_group.terminate",
                       side_effect=lambda group: self.terminated.append(group) or True),
            mock.patch("fileview.supervisor.reconcile.registry.forget"),
            mock.patch("fileview.supervisor.reconcile.control.close_viewer", return_value="closed"),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def running(self, groups):
        return mock.patch("fileview.supervisor.reconcile.registry.all_viewer_groups", return_value=groups)

    def test_viewer_of_an_unknown_session_is_stopped(self):
        with self.running({100: "ghost"}):
            reconcile.reconcile(self.state, now=1000)
        self.assertEqual(self.terminated, [100])

    def test_wanted_viewer_without_a_link_gets_a_grace_period_then_is_stopped(self):
        self.state.table.put(Session("s1", claude_pid=0))
        self.state.last_seen["s1"] = 1000
        with self.running({100: "s1"}):
            reconcile.reconcile(self.state, now=1000 + reconcile.GRACE_SECONDS - 1)
            self.assertEqual(self.terminated, [])
            reconcile.reconcile(self.state, now=1000 + reconcile.GRACE_SECONDS + 1)
        self.assertEqual(self.terminated, [100])

    def test_attached_viewer_is_left_alone(self):
        self.state.table.put(Session("s1"))
        self.state.attached["s1"] = object()
        with self.running({100: "s1"}):
            reconcile.reconcile(self.state, now=5000)
        self.assertEqual(self.terminated, [])

    def test_session_whose_claude_ended_is_closed_and_dropped(self):
        self.state.table.put(Session("s1", claude_pid=999999))
        with self.running({}), mock.patch("fileview.supervisor.reconcile.claude_alive", return_value=False):
            actions = reconcile.reconcile(self.state, now=1000)
        self.assertIsNone(self.state.table.get("s1"))
        self.assertIn("its Claude process ended", actions[0])

    def test_viewer_gone_past_grace_is_unwanted_not_reopened(self):
        self.state.table.put(Session("s1", claude_pid=0))
        self.state.last_seen["s1"] = 1000
        with self.running({}):
            reconcile.reconcile(self.state, now=1000 + reconcile.GRACE_SECONDS + 1)
        self.assertFalse(self.state.table.get("s1").wanted)


if __name__ == "__main__":
    unittest.main()
