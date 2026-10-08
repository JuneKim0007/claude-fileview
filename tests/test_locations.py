import unittest
from pathlib import Path

import fileview
from fileview import locations

CHECKOUT = Path(fileview.__file__).resolve().parent.parent


class CodeRelativePaths(unittest.TestCase):
    def test_processes_are_started_from_this_copy_of_the_code(self):
        self.assertEqual(locations.ENTRY_SCRIPT, CHECKOUT / "bin" / "fileview")
        self.assertTrue(locations.ENTRY_SCRIPT.is_file())

    def test_default_rules_file_belongs_to_this_copy(self):
        self.assertEqual(locations.DEFAULT_CONFIG, CHECKOUT / "default.yaml")


if __name__ == "__main__":
    unittest.main()
