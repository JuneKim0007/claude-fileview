import os
import unittest

from fileview.model.event import Event
from fileview.model.kind import Kind
from fileview.render.banner import banner
from fileview.render.line import format_event
from fileview.render.palette import Palette
from fileview.rules.defaults import DEFAULT_RULES
from fileview.rules.model import Match, PatternSet, Rules, TextRule

PLAIN = Palette(enabled=False, spec=DEFAULT_RULES.palette)
HOME = os.path.expanduser("~")


def lines(event, width=80, rules=DEFAULT_RULES):
    return format_event(event, "/repo", width, PLAIN, rules)


class Banner(unittest.TestCase):
    def test_fills_exactly_the_width(self):
        for width in (40, 80, 157):
            self.assertEqual(len(banner("File explorer history tools", width)), width)

    def test_long_title_is_elided_not_wrapped(self):
        self.assertEqual(len(banner("x" * 300, 60)), 60)


class Line(unittest.TestCase):
    def test_read_line_is_tag_then_root_relative_path(self):
        self.assertEqual(lines(Event(0, "s", "main", Kind.READ, "/repo/backend/Makefile", "", "/repo")),
                         ["[READ]   backend/Makefile"])

    def test_prefix_label_replaces_the_directory(self):
        event = Event(0, "s", "main", Kind.WRITE, f"{HOME}/.claude/fileview/fileview/cli.py", "", "/repo")
        self.assertEqual(lines(event), ["[WRITE]  [fileview] fileview/cli.py"])

    def test_subagent_is_named(self):
        self.assertTrue(lines(Event(0, "s", "Explore", Kind.READ, "/repo/a.ts", "", "/repo"))[0].endswith("<Explore>"))

    def test_line_never_exceeds_width(self):
        event = Event(0, "s", "main", Kind.WRITE, "/repo/" + "deep/" * 30 + "f.ts", "note " * 20, "/repo")
        self.assertLessEqual(len(lines(event, width=60)[0]), 60)

    def test_invoke_shows_command(self):
        self.assertEqual(lines(Event(0, "s", "main", Kind.INVOKE, "", "ls\npwd", "/repo")), ["[INVOKE] $ ls ; pwd"])

    def test_ignored_path_gives_no_lines(self):
        rules = Rules(ignore=PatternSet(glob=("*.lock",)))
        self.assertEqual(lines(Event(0, "s", "main", Kind.READ, "/repo/x.lock", "", "/repo"), rules=rules), [])

    def test_git_push_done_gives_one_full_width_banner_and_no_line(self):
        event = Event(0, "s", "main", Kind.DONE, "", "git push", "/repo",
                      {"push.branch": "main", "push.old": "1a2b3c4", "push.new": "5d6e7f8"})
        [banner_line] = lines(event, width=70)
        self.assertEqual(len(banner_line), 70)
        self.assertIn("[ git pushed main  1a2b3c4..5d6e7f8 ]", banner_line)

    def test_display_template_replaces_the_body_and_fits(self):
        rules = Rules(display=(TextRule(Match(kinds=("INVOKE",)), "<cyan>ran</> {command}"),))
        [line] = lines(Event(0, "s", "main", Kind.INVOKE, "", "make " + "x" * 200, "/repo"), width=50, rules=rules)
        self.assertTrue(line.startswith("[INVOKE] ran make x"))
        self.assertLessEqual(len(line), 50)


if __name__ == "__main__":
    unittest.main()
