import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fileview.config import config_file
from fileview.config.load import load_rules
from fileview.rules.defaults import DEFAULT_RULES
from fileview.rules.model import PatternSet

MALFORMED = "schemaVersion: 1\nignore: {glob: [3]}\n"


class FallbackPolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.user, self.default = base / "user" / "config.yaml", base / "default.yaml"
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        os.environ.pop("CLAUDE_FILEVIEW_CONFIG", None)
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def load(self, explicit=None, confirm=None):
        return load_rules(explicit, confirm, user_config=self.user, default_config=self.default)

    def test_nothing_exists_generates_both_files(self):
        loaded = self.load()
        self.assertEqual((loaded.rules, loaded.source, loaded.problems), (DEFAULT_RULES, str(self.user), []))
        self.assertTrue(self.user.is_file() and self.default.is_file())

    def test_valid_user_file_is_used(self):
        self.user.parent.mkdir(parents=True)
        self.user.write_text("schemaVersion: 1\nignore: {glob: ['*.lock']}\n")
        loaded = self.load()
        self.assertEqual(loaded.rules.ignore, PatternSet(glob=("*.lock",)))

    def test_malformed_user_file_without_an_answer_falls_back_and_is_kept(self):
        self.user.parent.mkdir(parents=True)
        self.user.write_text(MALFORMED)
        loaded = self.load(confirm=None)
        self.assertEqual(loaded.source, str(self.default))
        self.assertEqual([p.code for p in loaded.problems], ["wrong_type"])
        self.assertEqual(self.user.read_text(), MALFORMED)               # never overwritten unasked

    def test_malformed_user_file_answered_no_is_kept(self):
        self.user.parent.mkdir(parents=True)
        self.user.write_text(MALFORMED)
        loaded = self.load(confirm=lambda _question: False)
        self.assertEqual(loaded.source, str(self.default))
        self.assertEqual(self.user.read_text(), MALFORMED)

    def test_malformed_user_file_answered_yes_is_backed_up_and_regenerated(self):
        self.user.parent.mkdir(parents=True)
        self.user.write_text(MALFORMED)
        questions = []
        loaded = self.load(confirm=lambda question: questions.append(question) or True)
        self.assertEqual((loaded.source, loaded.rules), (str(self.user), DEFAULT_RULES))
        self.assertIn("ignore.glob[0]", questions[0])                    # the question says why
        [backup] = list(self.user.parent.glob("config.yaml.bak-*"))
        self.assertEqual(backup.read_text(), MALFORMED)

    def test_missing_explicit_file_is_reported_and_default_used(self):
        loaded = self.load(explicit=str(Path(self.tmp.name) / "nope.yaml"))
        self.assertEqual([p.code for p in loaded.problems], ["missing_file"])
        self.assertEqual(loaded.source, str(self.default))
        self.assertFalse(self.user.exists())                             # only the user file is generated

    def test_malformed_default_falls_back_to_built_ins(self):
        self.default.write_text("not: [valid\n")
        loaded = self.load(explicit=str(Path(self.tmp.name) / "nope.yaml"))
        self.assertEqual((loaded.rules, loaded.source), (DEFAULT_RULES, "built-in defaults"))
        self.assertEqual([p.code for p in loaded.problems], ["missing_file", "unreadable_yaml"])

    def test_missing_pyyaml_uses_built_ins(self):
        import fileview.config as package
        blocked = {"yaml": None, "fileview.config.yaml_codec": None, "fileview.config.config_file": None}
        with mock.patch.dict("sys.modules", blocked), mock.patch.dict(package.__dict__):
            package.__dict__.pop("config_file", None)        # already imported above: hide the cached attribute
            package.__dict__.pop("yaml_codec", None)
            loaded = self.load()
        self.assertEqual((loaded.source, loaded.problems[0].code), ("built-in defaults", "missing_dependency"))

    def test_as_dict_is_json_ready(self):
        self.user.parent.mkdir(parents=True)
        self.user.write_text(MALFORMED)
        data = self.load().as_dict()
        self.assertEqual(data["problems"][0]["path"], "ignore.glob[0]")


class Write(unittest.TestCase):
    def test_write_is_atomic_and_leaves_no_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = config_file.write(Path(tmp) / "c.yaml", DEFAULT_RULES)
            self.assertEqual(config_file.read(path), DEFAULT_RULES)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["c.yaml"])


if __name__ == "__main__":
    unittest.main()
