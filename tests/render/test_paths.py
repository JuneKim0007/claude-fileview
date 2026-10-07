import unittest

from fileview.render.paths import elide_middle


class ElideMiddle(unittest.TestCase):
    def test_keeps_the_file_name(self):
        text = elide_middle("backend/src/modules/admin/presentation/routes/admin.routes.ts", 30)
        self.assertLessEqual(len(text), 30)
        self.assertTrue(text.endswith("/admin.routes.ts"))
        self.assertIn("…", text)

    def test_short_text_is_unchanged(self):
        self.assertEqual(elide_middle("a/b.ts", 30), "a/b.ts")


if __name__ == "__main__":
    unittest.main()
