import json
import re
import tempfile
import unittest
from pathlib import Path

from fileview.capture.compiled_captures import CompiledCapture, load
from fileview.capture.hook_entry import events_for
from fileview.capture.output_capture import SCAN_CHARS, capture_values, output_text
from fileview.model.kind import Kind

PUSH = CompiledCapture("push", re.compile(r"git push (?P<remote>\S+)"),
                       re.compile(r"(?P<old>[0-9a-f]{7})\.\.(?P<new>[0-9a-f]{7})\s+(?P<branch>\S+)\s+->"))
PUSH_OUTPUT = "To github.com:x/y.git\n   1a2b3c4..5d6e7f8  main -> main\n"


class Values(unittest.TestCase):
    def test_named_groups_from_command_and_output(self):
        self.assertEqual(capture_values("git push origin", PUSH_OUTPUT, [PUSH]),
                         {"push.remote": "origin", "push.old": "1a2b3c4", "push.new": "5d6e7f8", "push.branch": "main"})

    def test_output_pattern_is_part_of_the_condition(self):
        self.assertEqual(capture_values("git push origin", "Everything up-to-date", [PUSH]), {})

    def test_other_commands_capture_nothing(self):
        self.assertEqual(capture_values("git status", PUSH_OUTPUT, [PUSH]), {})

    def test_only_the_tail_is_scanned(self):
        buried = PUSH_OUTPUT + "x" * (SCAN_CHARS + 10)
        self.assertEqual(capture_values("git push origin", buried, [PUSH]), {})   # output must match, so nothing

    def test_output_text_joins_stdout_and_stderr(self):
        self.assertEqual(output_text({"stdout": "a", "stderr": "b"}), "a\nb")


class CapturesFile(unittest.TestCase):
    def test_missing_or_bad_file_means_no_captures(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captures.json"
            self.assertEqual(load(path), [])
            path.write_text("{bad")
            self.assertEqual(load(path), [])
            path.write_text(json.dumps({"schemaVersion": 99, "captures": []}))
            self.assertEqual(load(path), [])
            path.write_text(json.dumps({"schemaVersion": 1, "captures": [{"name": "n", "command": "(", "output": ""}]}))
            self.assertEqual(load(path), [])                  # a bad regex disables capture, never the hook


class HookEvents(unittest.TestCase):
    def test_finished_bash_command_becomes_a_done_event(self):
        payload = {"hook_event_name": "PostToolUse", "session_id": "s1234567", "cwd": "/tmp", "tool_name": "Bash",
                   "tool_input": {"command": "echo hi"}, "tool_response": {"stdout": "hi"}}
        done = [e for e in events_for(payload) if e.kind is Kind.DONE]
        self.assertEqual([(e.detail, e.values) for e in done], [("echo hi", {})])

    def test_failed_bash_command_becomes_a_failed_event(self):
        payload = {"hook_event_name": "PostToolUseFailure", "session_id": "s1234567", "cwd": "/tmp",
                   "tool_name": "Bash", "tool_input": {"command": "false"}, "error": "exit 1"}
        self.assertEqual([e.kind for e in events_for(payload)], [Kind.FAILED])


if __name__ == "__main__":
    unittest.main()
