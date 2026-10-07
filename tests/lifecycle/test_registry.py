import unittest

from fileview.lifecycle.registry import viewer_session
from fileview.locations import ENTRY_SCRIPT, STATE_DIR

PYTHON = "/opt/homebrew/Cellar/python/Python.app/Contents/MacOS/Python"


class ViewerSession(unittest.TestCase):
    def test_python_viewer_of_this_state_dir_is_recognised(self):
        args = f"{PYTHON} -E -s {ENTRY_SCRIPT} view 0a762c2f --state {STATE_DIR}"
        self.assertEqual(viewer_session(args), "0a762c2f")

    def test_config_argument_does_not_change_the_session(self):
        args = f"{PYTHON} -E -s {ENTRY_SCRIPT} view 0a762c2f --config /x/c.yaml --state {STATE_DIR}"
        self.assertEqual(viewer_session(args), "0a762c2f")

    def test_viewer_of_another_state_dir_is_not_ours(self):
        args = f"{PYTHON} -E -s {ENTRY_SCRIPT} view 0a762c2f --state /tmp/other-state"
        self.assertIsNone(viewer_session(args))

    def test_shell_mentioning_a_viewer_is_not_one(self):
        args = f'/bin/zsh -c pgrep -fl "-E -s {ENTRY_SCRIPT} view 0a762c2f"'
        self.assertIsNone(viewer_session(args))

    def test_legacy_bash_viewers_are_recognised_for_cleanup(self):
        self.assertEqual(viewer_session("/bin/bash /Users/x/.claude/hooks/touched-view.sh 0a762c2f"), "0a762c2f")
        args = "claude-fileview 0a762c2f /Users/x/.claude/hooks/touched-view.sh 0a762c2f"
        self.assertEqual(viewer_session(args), "0a762c2f")

    def test_unrelated_process(self):
        self.assertIsNone(viewer_session("/usr/bin/tail -F /tmp/x"))


if __name__ == "__main__":
    unittest.main()
