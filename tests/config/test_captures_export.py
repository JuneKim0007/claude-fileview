import json
import tempfile
import unittest
from pathlib import Path

from fileview.config.captures_export import export
from fileview.rules.model import CaptureRule

RULES = (CaptureRule("push", r"git push (?P<remote>\S+)", r"(?P<branch>\S+) ->"), CaptureRule("status", "git status"))


class Export(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state" / "captures.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_the_hook_format_creating_the_directory(self):
        self.assertTrue(export(RULES, self.path))
        self.assertEqual(json.loads(self.path.read_text()), {"schemaVersion": 1, "captures": [
            {"name": "push", "command": r"git push (?P<remote>\S+)", "output": r"(?P<branch>\S+) ->"},
            {"name": "status", "command": "git status", "output": ""}]})

    def test_unchanged_content_is_not_rewritten(self):
        export(RULES, self.path)
        stamp = self.path.stat().st_mtime_ns
        self.assertFalse(export(RULES, self.path))
        self.assertEqual(self.path.stat().st_mtime_ns, stamp)

    def test_changed_content_is_rewritten_and_leaves_no_partial_file(self):
        export(RULES, self.path)
        self.assertTrue(export(RULES[:1], self.path))
        self.assertEqual(len(json.loads(self.path.read_text())["captures"]), 1)
        self.assertEqual(sorted(p.name for p in self.path.parent.iterdir()), ["captures.json"])


if __name__ == "__main__":
    unittest.main()
