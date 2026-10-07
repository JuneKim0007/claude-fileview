"""The override order (rules/pipeline.py), one test per rule of it."""
import unittest

from fileview.model.event import Event
from fileview.model.kind import Kind
from fileview.rules.model import ColourRule, Match, PatternSet, Rules, TextRule
from fileview.rules.pipeline import plan


def read(path, **kw):
    return Event(0, "s", "main", Kind.READ, path, "", "/repo", **kw)


def command(kind, text, values=None):
    return Event(0, "s", "main", kind, "", text, "/repo", values or {})


def texts(parts_list):
    return ["".join(p.data for p in parts if p.kind == "text") for parts in parts_list]


class Visibility(unittest.TestCase):
    def test_ignore_hides_by_path_glob_and_regex(self):
        rules = Rules(ignore=PatternSet(glob=("*.lock",), regex=(r"/node_modules/",)))
        self.assertIsNone(plan(read("/repo/yarn.lock"), rules, "/repo"))
        self.assertIsNone(plan(read("/repo/node_modules/x.js"), rules, "/repo"))
        self.assertIsNotNone(plan(read("/repo/src/x.js"), rules, "/repo"))

    def test_deignore_beats_ignore_whatever_the_order(self):
        rules = Rules(ignore=PatternSet(glob=("*",)), deignore=PatternSet(glob=("*.md",)))
        self.assertIsNotNone(plan(read("/repo/AGENTS.md"), rules, "/repo"))
        self.assertIsNone(plan(read("/repo/Makefile"), rules, "/repo"))

    def test_ignore_by_kind_and_command(self):
        rules = Rules(ignore=PatternSet(match=(Match(kinds=("INVOKE",), command=r"^ls\b"),)))
        self.assertIsNone(plan(command(Kind.INVOKE, "ls -la"), rules, "/repo"))
        self.assertIsNotNone(plan(command(Kind.INVOKE, "make test"), rules, "/repo"))

    def test_path_shorthands_never_hide_commands(self):
        rules = Rules(ignore=PatternSet(glob=("*",)))
        self.assertIsNotNone(plan(command(Kind.INVOKE, "ls"), rules, "/repo"))


class Announce(unittest.TestCase):
    PUSH = Match(kinds=("DONE",), command=r"git push")

    def test_every_matching_banner_fires_in_order(self):
        rules = Rules(announce=(TextRule(self.PUSH, "first"), TextRule(Match(), "second")))
        self.assertEqual(texts(plan(command(Kind.DONE, "git push"), rules, "/repo").banners), ["first", "second"])

    def test_values_fill_the_banner(self):
        rules = Rules(announce=(TextRule(self.PUSH, "<yellow>pushed</> {push.branch} {push.new}"),))
        event = command(Kind.DONE, "git push", {"push.branch": "main", "push.new": "def5678"})
        self.assertEqual(texts(plan(event, rules, "/repo").banners), ["pushed main def5678"])

    def test_a_banner_with_a_missing_value_does_not_fire(self):
        rules = Rules(announce=(TextRule(self.PUSH, "pushed {push.new}"),))
        self.assertEqual(plan(command(Kind.DONE, "git push"), rules, "/repo").banners, ())

    def test_banners_obey_ignore(self):
        rules = Rules(ignore=PatternSet(match=(Match(kinds=("DONE",)),)), announce=(TextRule(self.PUSH, "pushed"),))
        self.assertIsNone(plan(command(Kind.DONE, "git push"), rules, "/repo"))


class Display(unittest.TestCase):
    def test_first_complete_display_rule_replaces_the_body(self):
        rules = Rules(display=(TextRule(Match(command="make"), "needs {nope.x}"),
                               TextRule(Match(command="make"), "tests: {command}"),
                               TextRule(Match(), "never")))
        self.assertEqual(texts([plan(command(Kind.INVOKE, "make test"), rules, "/repo").body]), ["tests: make test"])

    def test_done_draws_no_line_unless_a_display_rule_gives_one(self):
        self.assertFalse(plan(command(Kind.DONE, "ls"), Rules(), "/repo").show_line)
        rules = Rules(display=(TextRule(Match(kinds=("DONE",)), "finished {command}"),))
        self.assertTrue(plan(command(Kind.DONE, "ls"), rules, "/repo").show_line)

    def test_failed_draws_a_line_by_default(self):
        self.assertTrue(plan(command(Kind.FAILED, "make"), Rules(), "/repo").show_line)


class Colour(unittest.TestCase):
    def test_first_colour_rule_wins_and_is_independent_of_visibility(self):
        rules = Rules(colour=(ColourRule("purple", glob="*.md"), ColourRule("red", regex="README")))
        self.assertEqual(plan(read("/repo/README.md"), rules, "/repo").path_colour, "purple")
        self.assertEqual(plan(read("/repo/README.txt"), rules, "/repo").path_colour, "red")
        hidden = Rules(ignore=PatternSet(glob=("*.md",)), colour=rules.colour)
        self.assertIsNone(plan(read("/repo/a.md"), hidden, "/repo"))


if __name__ == "__main__":
    unittest.main()
