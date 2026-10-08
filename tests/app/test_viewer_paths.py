import os
import unittest

from fileview.app.viewer import _home_short

HOME = os.path.expanduser("~")


class HomeShort(unittest.TestCase):
    def test_paths_under_home_use_tilde(self):
        self.assertEqual(_home_short(f"{HOME}/repo"), "~/repo")
        self.assertEqual(_home_short(HOME), "~")

    def test_a_sibling_sharing_the_home_prefix_is_left_alone(self):
        self.assertEqual(_home_short(f"{HOME}X/repo"), f"{HOME}X/repo")

    def test_paths_outside_home_are_unchanged(self):
        self.assertEqual(_home_short("/opt/repo"), "/opt/repo")


if __name__ == "__main__":
    unittest.main()
