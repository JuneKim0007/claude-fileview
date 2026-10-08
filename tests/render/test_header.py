import unittest

from fileview.render.header import HeaderStatus, header
from fileview.render.palette import Palette
from fileview.rules.defaults import DEFAULT_RULES

PLAIN = Palette(enabled=False, spec=DEFAULT_RULES.palette)


def draw(title, source, problems, notes, width=40):
    return header(title, "0a762c2f", width, PLAIN, HeaderStatus(source, problems, notes)).split("\n")


class Header(unittest.TestCase):
    def test_banner_legend_and_source(self):
        lines = draw("File tools", "/x/config.yaml", [], [])
        self.assertEqual(lines[0], "")
        self.assertEqual(len(lines[1]), 40)
        self.assertIn("[ File tools  ·  0a762c2f ]", lines[1])
        self.assertEqual(lines[2], "[READ] [WRITE] [CREATE] [DELETE] [SEARCH] [INVOKE] [DONE] [FAILED] [LOAD]")
        self.assertEqual(lines[3:], ["rules /x/config.yaml"])

    def test_problems_then_notes_follow_the_source(self):
        lines = draw(None, "built-in defaults", ["wrong_type: f at a.b"], ["generated f"])
        self.assertIn("[ session 0a762c2f ]", lines[1])
        self.assertEqual(lines[3:], ["rules built-in defaults", "config: wrong_type: f at a.b", "config: generated f"])

    def test_colours_problems_yellow_and_notes_dim(self):
        coloured = Palette(enabled=True, spec=DEFAULT_RULES.palette)
        lines = header(None, "s", 40, coloured, HeaderStatus("src", ["bad"], ["note"])).split("\n")
        self.assertEqual(lines[4], "\033[33mconfig: bad\033[0m")
        self.assertEqual(lines[5], "\033[2mconfig: note\033[0m")


if __name__ == "__main__":
    unittest.main()
