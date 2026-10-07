import unittest

from fileview.capture.bash_diff import UNATTRIBUTED, bash_diff_events
from fileview.capture.context import HookContext
from fileview.model.kind import Kind

CTX = HookContext(session="s1", agent="main", cwd="/repo", root="/repo", ts=0.0)


class BashDiffEvents(unittest.TestCase):
    def test_flags_map_to_kinds(self):
        response = {"bashEditDiff": {"files": [
            {"filePath": "/repo/old.txt", "deleted": True},
            {"filePath": "/repo/gen.ts", "created": True},
            {"filePath": "/repo/a.ts"},
        ]}}
        events = bash_diff_events(CTX, "rm old.txt; touch gen.ts; sed -i x a.ts", response)
        self.assertEqual([e.kind for e in events], [Kind.DELETE, Kind.CREATE, Kind.WRITE])
        self.assertTrue(all(e.detail == "" for e in events))

    def test_file_the_command_does_not_name_is_marked_unattributed(self):
        response = {"bashEditDiff": {"files": [{"filePath": "/repo/admin.module.ts"}]}}
        [event] = bash_diff_events(CTX, "fileview open; sleep 1", response)
        self.assertEqual(event.detail, UNATTRIBUTED)

    def test_changed_files_outside_files_list_and_overflow(self):
        response = {"bashEditDiff": {"files": [{"filePath": "/repo/a.ts"}],
                                     "changedFiles": ["/repo/a.ts", "/repo/b.ts"], "moreFiles": 2}}
        events = bash_diff_events(CTX, "x a.ts b.ts", response)
        self.assertEqual([e.path for e in events], ["/repo/a.ts", "/repo/b.ts", ""])
        self.assertEqual(events[-1].detail, "... +2 more files")

    def test_non_dict_response_yields_nothing(self):
        self.assertEqual(bash_diff_events(CTX, "ls", "plain text"), [])


if __name__ == "__main__":
    unittest.main()
