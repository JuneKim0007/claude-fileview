import os
import tempfile
import unittest
from pathlib import Path

from fileview.store.follower import follow
from fileview.store.rotation import rotate_if_large


def take(stream, count):
    lines = []
    for _ in range(count * 20):
        item = next(stream)
        if item is not None:
            lines.append(item.strip())
            if len(lines) == count:
                break
    return lines


class Follower(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = Path(self.tmp.name) / "events.jsonl"
        self.log.write_text("a\nb\n")

    def tearDown(self):
        self.tmp.cleanup()

    def append(self, text):
        with open(self.log, "a") as handle:
            handle.write(text)

    def test_backfill_then_new_lines(self):
        stream = follow(self.log)
        self.addCleanup(stream.close)
        self.assertEqual(take(stream, 2), ["a", "b"])
        self.append("c\n")
        self.assertEqual(take(stream, 1), ["c"])

    def test_partial_line_waits_for_its_end(self):
        stream = follow(self.log)
        self.addCleanup(stream.close)
        take(stream, 2)
        self.append("par")
        self.assertIsNone(next(stream))
        self.append("tial\n")
        self.assertEqual(take(stream, 1), ["partial"])

    def test_survives_rotation(self):
        stream = follow(self.log)
        self.addCleanup(stream.close)
        take(stream, 2)
        rotate_if_large(self.log, max_bytes=0)
        self.assertTrue(os.path.exists(str(self.log) + ".1"))
        self.append("after-rotation\n")
        self.assertEqual(take(stream, 1), ["after-rotation"])


if __name__ == "__main__":
    unittest.main()
