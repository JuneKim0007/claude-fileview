import unittest

from fileview.rules.colours import sgr


class Sgr(unittest.TestCase):
    def test_built_in_name(self):
        self.assertEqual(sgr("green"), "32")

    def test_index_and_hex(self):
        self.assertEqual(sgr(208), "38;5;208")
        self.assertEqual(sgr("#af87ff"), "38;2;175;135;255")

    def test_custom_name_points_at_a_colour(self):
        self.assertEqual(sgr("lavender", {"lavender": "#af87ff"}), "38;2;175;135;255")

    def test_rejects_unknown_and_out_of_range(self):
        for bad in ("chartreuse", 256, -1, True, "#12345"):
            with self.assertRaises(ValueError):
                sgr(bad)


if __name__ == "__main__":
    unittest.main()
