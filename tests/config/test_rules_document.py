import unittest

from fileview.config import rules_document
from fileview.config.errors import ConfigError
from fileview.rules.defaults import DEFAULT_RULES
from fileview.rules.model import ColourRule, PatternSet, Prefix


def parse(document):
    return rules_document.parse({"schemaVersion": 1, **document})


def failure(document):
    with self_raises() as caught:
        parse(document)
    return caught.exception


class self_raises:
    def __enter__(self):
        return self

    def __exit__(self, kind, value, _traceback):
        if not isinstance(value, ConfigError):
            raise AssertionError(f"expected ConfigError, got {kind}")
        self.exception = value
        return True


class Parse(unittest.TestCase):
    def test_defaults_round_trip(self):
        self.assertEqual(rules_document.parse(rules_document.of(DEFAULT_RULES)), DEFAULT_RULES)

    def test_empty_document_means_no_rules_and_default_palette(self):
        rules = parse({})
        self.assertEqual((rules.prefixes, rules.ignore, rules.colour), ((), PatternSet(), ()))
        self.assertEqual(rules.palette.kinds, DEFAULT_RULES.palette.kinds)

    def test_full_document(self):
        rules = parse({
            "palette": {"kinds": {"READ": "#00ff00"}, "label": 141, "colours": {"lavender": "#af87ff"}},
            "prefixes": [{"path": "~/x", "label": "x", "colour": "lavender"}],
            "ignore": {"glob": ["*.lock"], "regex": [r"/node_modules/"]},
            "deignore": {"glob": ["*/package-lock.json"]},
            "colour": [{"glob": "*.md", "colour": "lavender"}, {"regex": r"\.ya?ml$", "colour": "yellow"}],
        })
        self.assertEqual(rules.palette.kinds["READ"], "#00ff00")
        self.assertEqual(rules.palette.kinds["WRITE"], "blue")          # unspecified kinds keep the default
        self.assertEqual(rules.prefixes, (Prefix("~/x", "x", "lavender"),))
        self.assertEqual(rules.ignore, PatternSet(("*.lock",), (r"/node_modules/",)))
        self.assertEqual(rules.colour[1], ColourRule("yellow", regex=r"\.ya?ml$"))


class Rejections(unittest.TestCase):
    def check(self, document, code, path):
        problem = failure(document)
        self.assertEqual((problem.code, problem.path), (code, path))

    def test_unknown_section(self):
        self.check({"ignored": {}}, "unknown_keys", "(top level)")

    def test_unknown_key_inside_a_section(self):
        self.check({"ignore": {"globs": []}}, "unknown_keys", "ignore")

    def test_wrong_type_names_the_item(self):
        self.check({"ignore": {"glob": ["*.lock", 3]}}, "wrong_type", "ignore.glob[1]")

    def test_bad_regex(self):
        self.check({"deignore": {"regex": ["(unclosed"]}}, "bad_regex", "deignore.regex[0]")

    def test_unknown_colour(self):
        self.check({"colour": [{"glob": "*.md", "colour": "chartreuse"}]}, "unknown_colour", "colour[0].colour")

    def test_unknown_kind_in_palette(self):
        self.check({"palette": {"kinds": {"READS": "green"}}}, "unknown_keys", "palette.kinds")

    def test_colour_rule_needs_exactly_one_matcher(self):
        self.check({"colour": [{"glob": "*.md", "regex": "x", "colour": "red"}]}, "wrong_type", "colour[0]")

    def test_prefix_needs_a_label(self):
        self.check({"prefixes": [{"path": "~/x"}]}, "missing_field", "prefixes[0].label")


if __name__ == "__main__":
    unittest.main()
