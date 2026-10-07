import os
import unittest

from fileview.rules.defaults import DEFAULT_RULES
from fileview.rules.model import ColourRule, PatternSet, Prefix, Rules
from fileview.rules.resolve import resolve

HOME = os.path.expanduser("~")


class Locate(unittest.TestCase):
    def test_inside_root_is_relative_and_unlabelled(self):
        view = resolve("/repo/backend/package.json", "/repo", DEFAULT_RULES)
        self.assertEqual((view.label, view.rest), ("", "backend/package.json"))

    def test_root_prefix_must_be_a_whole_directory(self):
        self.assertEqual(resolve("/repo-other/a.ts", "/repo", DEFAULT_RULES).rest, "/repo-other/a.ts")

    def test_longest_prefix_wins(self):
        view = resolve(f"{HOME}/.claude/fileview/fileview/cli.py", "/repo", DEFAULT_RULES)
        self.assertEqual((view.label, view.rest), ("fileview", "fileview/cli.py"))
        view = resolve(f"{HOME}/.claude/settings.json", "/repo", DEFAULT_RULES)
        self.assertEqual((view.label, view.rest), ("claude", "settings.json"))

    def test_root_beats_a_prefix_that_contains_it(self):
        rules = Rules(prefixes=(Prefix("/work", "work"),))
        self.assertEqual(resolve("/work/repo/a.ts", "/work/repo", rules).label, "")

    def test_prefix_highlight_colour_is_carried(self):
        rules = Rules(prefixes=(Prefix("/opt/tools", "tools", "cyan"),))
        self.assertEqual(resolve("/opt/tools/x", "/repo", rules).label_colour, "cyan")

    def test_unprefixed_home_path_uses_tilde(self):
        view = resolve(f"{HOME}/notes/todo.txt", "/repo", Rules())
        self.assertEqual((view.label, view.rest), ("", "~/notes/todo.txt"))


class Visibility(unittest.TestCase):
    def test_ignore_by_glob_and_regex(self):
        rules = Rules(ignore=PatternSet(glob=("*.lock",), regex=(r"/node_modules/",)))
        self.assertFalse(resolve("/repo/yarn.lock", "/repo", rules).visible)
        self.assertFalse(resolve("/repo/node_modules/x/i.js", "/repo", rules).visible)
        self.assertTrue(resolve("/repo/src/i.js", "/repo", rules).visible)

    def test_deignore_overrules_ignore(self):
        rules = Rules(ignore=PatternSet(glob=("*",)), deignore=PatternSet(glob=("*.md",)))
        self.assertTrue(resolve("/repo/AGENTS.md", "/repo", rules).visible)
        self.assertFalse(resolve("/repo/Makefile", "/repo", rules).visible)

    def test_deignore_by_regex(self):
        rules = Rules(ignore=PatternSet(regex=(r"\.json$",)), deignore=PatternSet(regex=(r"/package\.json$",)))
        self.assertTrue(resolve("/repo/package.json", "/repo", rules).visible)
        self.assertFalse(resolve("/repo/tsconfig.json", "/repo", rules).visible)

    def test_deignore_alone_hides_nothing(self):
        self.assertTrue(resolve("/repo/a.ts", "/repo", Rules(deignore=PatternSet(glob=("*.md",)))).visible)

    def test_glob_with_tilde_is_expanded(self):
        rules = Rules(ignore=PatternSet(glob=("~/.claude/*",)))
        self.assertFalse(resolve(f"{HOME}/.claude/x.json", "/repo", rules).visible)


class Colour(unittest.TestCase):
    def test_first_matching_rule_wins(self):
        rules = Rules(colour=(ColourRule("purple", glob="*.md"), ColourRule("red", regex=r"README")))
        self.assertEqual(resolve("/repo/README.md", "/repo", rules).colour, "purple")
        self.assertEqual(resolve("/repo/README.txt", "/repo", rules).colour, "red")

    def test_colour_is_independent_of_visibility(self):
        rules = Rules(ignore=PatternSet(glob=("*.md",)), colour=(ColourRule("purple", glob="*.md"),))
        view = resolve("/repo/a.md", "/repo", rules)
        self.assertEqual((view.colour, view.visible), ("purple", False))


if __name__ == "__main__":
    unittest.main()
