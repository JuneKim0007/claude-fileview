"""A real supervisor process in a throwaway state directory. Terminal variables are removed, so no
window is ever opened; viewers are stood in for by a process holding a link."""
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ENTRY = str(Path(__file__).resolve().parents[2] / "bin" / "fileview")
ATTACH = """
import sys, time
from fileview.supervisor.link import SupervisorLink
link = SupervisorLink.attach(sys.argv[1])
print("attached", flush=True)
while link.alive():
    time.sleep(0.05)
print("link closed", flush=True)
"""


class RealSupervisor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {k: v for k, v in os.environ.items() if k not in ("TERM_PROGRAM", "TMUX", "CLAUDE_FILEVIEW_CONFIG")}
        self.env["CLAUDE_FILEVIEW_STATE"] = self.tmp.name
        self.addCleanup(self._stop)

    def _stop(self):
        self.fileview("supervisor", "stop")
        self.tmp.cleanup()

    def fileview(self, *args):
        return subprocess.run([sys.executable, "-E", "-s", ENTRY, *args], env=self.env,
                              capture_output=True, text=True, timeout=30)

    def attach(self, session):
        process = subprocess.Popen([sys.executable, "-E", "-s", "-c", ATTACH, session], env=self.env,
                                   cwd=str(Path(ENTRY).parents[1]), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True)
        self.addCleanup(process.kill)
        return process

    def test_starts_on_demand_and_stays_up(self):
        self.assertIn("supervisor down", self.fileview("supervisor", "status").stdout)
        self.assertEqual(self.fileview("list").returncode, 0)                       # first use starts it
        status = self.fileview("supervisor", "status").stdout
        self.assertIn("supervisor up", status)
        time.sleep(1)
        self.assertIn("supervisor up", self.fileview("supervisor", "status").stdout)

    def test_no_supervisor_means_a_viewer_cannot_attach(self):
        process = self.attach("s1")
        _, err = process.communicate(timeout=10)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("SupervisorUnavailable", err)

    def test_viewers_exit_when_the_supervisor_dies(self):
        self.fileview("list")
        viewer = self.attach("s1")
        self.assertEqual(viewer.stdout.readline().strip(), "attached")
        pid = int(Path(self.tmp.name, "supervisor.lock").read_text())
        os.kill(pid, 9)                                       # a crash, not a polite stop
        self.assertEqual(viewer.stdout.readline().strip(), "link closed")
        viewer.wait(timeout=5)

    def test_kill_works_without_a_responsive_supervisor_and_clears_everything(self):
        self.fileview("list")
        pid = int(Path(self.tmp.name, "supervisor.lock").read_text())
        os.kill(pid, 19)                                      # SIGSTOP: wedged, cannot answer anything
        try:
            result = self.fileview("kill")
        finally:
            try:
                os.kill(pid, 18)
            except ProcessLookupError:
                pass
        self.assertIn("supervisor stopped", result.stdout)
        self.assertIn("supervisor down", self.fileview("supervisor", "status").stdout)
        self.assertFalse(Path(self.tmp.name, "supervisor.sock").exists())

    def test_second_supervisor_refuses_to_run(self):
        self.fileview("list")
        second = self.fileview("supervisor", "run")
        self.assertEqual(second.returncode, 1)


if __name__ == "__main__":
    unittest.main()
