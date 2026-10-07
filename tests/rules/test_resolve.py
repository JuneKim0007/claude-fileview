import os
import unittest

from fileview.rules.defaults import DEFAULT_RULES
from fileview.rules.model import Prefix, Rules
from fileview.rules.resolve import place

HOME = os.path.expanduser("~")


class Placement(unittest.TestCase):
    def test_inside_root_is_relative_and_unlabelled(self):
        placed = place("/repo/backend/package.json", "/repo", DEFAULT_RULES)
        self.assertEqual((placed.label, placed.rest, placed.text()), ("", "backend/package.json", "backend/package.json"))

    def test_root_prefix_must_be_a_whole_directory(self):
        self.assertEqual(place("/repo-other/a.ts", "/repo", DEFAULT_RULES).rest, "/repo-other/a.ts")

    def test_longest_prefix_wins(self):
        placed = place(f"{HOME}/.claude/fileview/fileview/cli.py", "/repo", DEFAULT_RULES)
        self.assertEqual(placed.text(), "[fileview] fileview/cli.py")
        self.assertEqual(place(f"{HOME}/.claude/settings.json", "/repo", DEFAULT_RULES).label, "claude")

    def test_root_beats_a_prefix_that_contains_it(self):
        self.assertEqual(place("/work/repo/a.ts", "/work/repo", Rules(prefixes=(Prefix("/work", "work"),))).label, "")

    def test_prefix_highlight_colour_is_carried(self):
        rules = Rules(prefixes=(Prefix("/opt/tools", "tools", "cyan"),))
        self.assertEqual(place("/opt/tools/x", "/repo", rules).label_colour, "cyan")

    def test_unprefixed_home_path_uses_tilde(self):
        self.assertEqual(place(f"{HOME}/notes/todo.txt", "/repo", Rules()).rest, "~/notes/todo.txt")


if __name__ == "__main__":
    unittest.main()
