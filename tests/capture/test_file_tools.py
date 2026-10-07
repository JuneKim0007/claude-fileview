import unittest

from fileview.capture.context import HookContext
from fileview.capture.file_tools import file_tool_events
from fileview.model.kind import Kind

CTX = HookContext(session="s1", agent="main", cwd="/repo/backend", root="/repo", ts=0.0)


class FileToolEvents(unittest.TestCase):
    def test_read_records_absolute_path_and_line_range(self):
        [event] = file_tool_events(CTX, "Read", {"file_path": "/repo/Makefile", "offset": 5, "limit": 20}, {})
        self.assertEqual((event.kind, event.path, event.detail), (Kind.READ, "/repo/Makefile", "lines 5+20"))

    def test_relative_path_resolves_against_cwd(self):
        [event] = file_tool_events(CTX, "Read", {"file_path": "Makefile"}, {})
        self.assertEqual(event.path, "/repo/backend/Makefile")

    def test_write_distinguishes_create_from_update(self):
        [created] = file_tool_events(CTX, "Write", {"file_path": "/repo/a.ts"}, {"type": "create"})
        [updated] = file_tool_events(CTX, "Write", {"file_path": "/repo/a.ts"}, {"type": "update"})
        self.assertEqual((created.kind, updated.kind), (Kind.CREATE, Kind.WRITE))

    def test_edit_is_write(self):
        [event] = file_tool_events(CTX, "Edit", {"file_path": "/repo/a.ts"}, {})
        self.assertEqual(event.kind, Kind.WRITE)

    def test_grep_is_search_with_pattern(self):
        [event] = file_tool_events(CTX, "Grep", {"pattern": "todo", "path": "src"}, {})
        self.assertEqual((event.kind, event.path, event.detail), (Kind.SEARCH, "/repo/backend/src", '"todo"'))


if __name__ == "__main__":
    unittest.main()
