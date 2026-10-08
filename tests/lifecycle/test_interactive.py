import os
import subprocess
import unittest
from unittest import mock

from fileview.lifecycle.interactive import is_interactive


def fake_ps(args_line: str, tty: str):
    """Answer `ps -o <field> -p <pid>` the way macOS ps does, whichever module asks."""
    def run(argv, **_kwargs):
        field = argv[argv.index("-o") + 1]
        out = args_line if field.startswith("args") else tty
        return subprocess.CompletedProcess(argv, 0, stdout=out + "\n", stderr="")
    return run


class Interactive(unittest.TestCase):
    def check(self, env: dict, args_line: str = "claude", tty: str = "ttys002") -> bool:
        with mock.patch.dict(os.environ, env, clear=False), \
             mock.patch("subprocess.run", side_effect=fake_ps(args_line, tty)):
            for key in ("CLAUDE_CODE_SESSION_ATTENDED", "CLAUDE_PID"):
                if key not in env:
                    os.environ.pop(key, None)
            return is_interactive()

    def test_unattended_session_is_not_interactive(self):
        self.assertFalse(self.check({"CLAUDE_CODE_SESSION_ATTENDED": "0", "CLAUDE_PID": "7"}))

    def test_no_claude_pid_counts_as_interactive(self):
        self.assertTrue(self.check({}))

    def test_print_mode_is_not_interactive(self):
        self.assertFalse(self.check({"CLAUDE_PID": "7"}, args_line="claude -p hello"))
        self.assertFalse(self.check({"CLAUDE_PID": "7"}, args_line="claude --print hello"))

    def test_no_terminal_is_not_interactive(self):
        self.assertFalse(self.check({"CLAUDE_PID": "7"}, tty="??"))
        self.assertFalse(self.check({"CLAUDE_PID": "7"}, tty=""))

    def test_a_claude_on_a_terminal_is_interactive(self):
        self.assertTrue(self.check({"CLAUDE_PID": "7"}, args_line="claude --continue", tty="ttys002"))


if __name__ == "__main__":
    unittest.main()
