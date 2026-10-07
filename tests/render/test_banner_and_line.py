import os
import unittest

from fileview.model.event import Event
from fileview.model.kind import Kind
from fileview.render.banner import banner
from fileview.render.line import format_line
from fileview.render.palette import Palette
from fileview.rules.defaults import DEFAULT_RULES
from fileview.rules.model import PatternSet, Rules

PLAIN = Palette(enabled=False, spec=DEFAULT_RULES.palette)
HOME = os.path.expanduser("~")


def line(event, width=80, rules=DEFAULT_RULES):
    return format_line(event, "/repo", width, PLAIN, rules)


class Banner(unittest.TestCase):
    def test_fills_exactly_the_width(self):
        for width in (40, 80, 157):
            self.assertEqual(len(banner("File explorer history tools", width)), width)

    def test_long_title_is_elided_not_wrapped(self):
        self.assertEqual(len(banner("x" * 300, 60)), 60)


class Line(unittest.TestCase):
    def test_read_line_is_tag_then_root_relative_path(self):
        self.assertEqual(line(Event(0, "s", "main", Kind.READ, "/repo/backend/Makefile", "", "/repo")),
                         "[READ]   backend/Makefile")

    def test_prefix_label_replaces_the_directory(self):
        event = Event(0, "s", "main", Kind.WRITE, f"{HOME}/.claude/fileview/fileview/cli.py", "", "/repo")
        self.assertEqual(line(event), "[WRITE]  [fileview] fileview/cli.py")

    def test_subagent_is_named(self):
        self.assertTrue(line(Event(0, "s", "Explore", Kind.READ, "/repo/a.ts", "", "/repo")).endswith("<Explore>"))

    def test_line_never_exceeds_width(self):
        event = Event(0, "s", "main", Kind.WRITE, "/repo/" + "deep/" * 30 + "f.ts", "note " * 20, "/repo")
        self.assertLessEqual(len(line(event, width=60)), 60)

    def test_invoke_shows_command_and_ignores_path_rules(self):
        rules = Rules(ignore=PatternSet(glob=("*",)))
        self.assertEqual(line(Event(0, "s", "main", Kind.INVOKE, "", "ls\npwd", "/repo"), rules=rules),
                         "[INVOKE] $ ls ; pwd")

    def test_ignored_path_gives_no_line(self):
        rules = Rules(ignore=PatternSet(glob=("*.lock",)))
        self.assertIsNone(line(Event(0, "s", "main", Kind.READ, "/repo/x.lock", "", "/repo"), rules=rules))


if __name__ == "__main__":
    unittest.main()
