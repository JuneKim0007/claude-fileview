import unittest

from fileview.config.errors import ConfigError
from fileview.config.yaml_codec import dump, load


class Load(unittest.TestCase):
    def test_mapping_loads(self):
        self.assertEqual(load("a: 1\nb: [x]\n", "f.yaml"), {"a": 1, "b": ["x"]})

    def test_duplicate_key_is_rejected_with_its_line(self):
        with self.assertRaises(ConfigError) as caught:
            load("a: 1\nb: 2\na: 3\n", "f.yaml")
        self.assertEqual(caught.exception.code, "unreadable_yaml")
        self.assertIn("duplicate key 'a'", caught.exception.detail)
        self.assertIn("line 3", caught.exception.detail)

    def test_syntax_error_reports_position(self):
        with self.assertRaises(ConfigError) as caught:
            load("a: [1, 2\n", "f.yaml")
        self.assertEqual(caught.exception.code, "unreadable_yaml")
        self.assertIn("line", caught.exception.detail)

    def test_non_mapping_document(self):
        with self.assertRaises(ConfigError) as caught:
            load("- a\n- b\n", "f.yaml")
        self.assertEqual(caught.exception.code, "not_a_mapping")

    def test_unsafe_tags_are_refused(self):
        with self.assertRaises(ConfigError):
            load("a: !!python/object/apply:os.system ['true']\n", "f.yaml")

    def test_dump_round_trips(self):
        document = {"schemaVersion": 1, "ignore": {"glob": ["*.lock"], "regex": []}}
        self.assertEqual(load(dump(document), "f.yaml"), document)


if __name__ == "__main__":
    unittest.main()
