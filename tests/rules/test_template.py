import unittest

from fileview.rules.template import Part, capture_fields, parse


class Parsing(unittest.TestCase):
    def test_colours_values_and_resets(self):
        template = parse("<yellow>pushed</> {push.new} done")
        self.assertEqual(template.parts, (Part("colour", "yellow"), Part("text", "pushed"), Part("reset"),
                                          Part("text", " "), Part("value", "push.new"), Part("text", " done")))
        self.assertEqual((template.placeholders(), template.colours()), ({"push.new"}, {"yellow"}))

    def test_escapes_are_literal(self):
        self.assertEqual(parse("{{x}} <<b>>").fill({}), (Part("text", "{"), Part("text", "x"), Part("text", "}"),
                                                         Part("text", " "), Part("text", "<"), Part("text", "b"),
                                                         Part("text", ">")))

    def test_fill_needs_every_placeholder(self):
        self.assertIsNone(parse("{a} {b}").fill({"a": "1"}))

    def test_values_are_never_reparsed(self):
        filled = parse("{command}").fill({"command": "echo <red>{x}</>"})
        self.assertEqual(filled, (Part("text", "echo <red>{x}</>"),))

    def test_capture_fields_from_named_groups(self):
        self.assertEqual(capture_fields("push", r"git push (?P<remote>\S+)", r"(?P<new>[0-9a-f]+)"),
                         {"push.remote", "push.new"})


if __name__ == "__main__":
    unittest.main()
