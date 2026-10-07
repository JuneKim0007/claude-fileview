import os
import tempfile
import unittest

from fileview.capture.bash_reads import bash_read_events
from fileview.capture.context import HookContext


class BashReadEvents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        os.makedirs(os.path.join(self.root, "backend"))
        for name in ("Makefile", "backend/Makefile", ".nvmrc", "my file.txt"):
            open(os.path.join(self.root, name), "w").close()
        self.ctx = HookContext(session="s", agent="main", cwd=self.root, root=self.root, ts=0.0)

    def tearDown(self):
        self.tmp.cleanup()

    def paths(self, command):
        return [os.path.relpath(e.path, self.root) for e in bash_read_events(self.ctx, command)]

    def test_reads_existing_files_and_skips_missing_and_flags(self):
        self.assertEqual(self.paths("cat Makefile | grep -n test; sed -n 1,5p .nvmrc nosuchfile"),
                         ["Makefile", ".nvmrc"])

    def test_cd_moves_the_base_for_later_commands(self):
        self.assertEqual(self.paths("cd backend && cat Makefile"), ["backend/Makefile"])

    def test_quoted_names_with_spaces(self):
        self.assertEqual(self.paths('head -3 "my file.txt"'), ["my file.txt"])

    def test_non_reader_programs_are_ignored(self):
        self.assertEqual(self.paths("rm Makefile; make test"), [])

    def test_unbalanced_quotes_give_no_inference(self):
        self.assertEqual(self.paths("cat 'Makefile"), [])

    def test_output_redirect_target_is_not_a_read(self):
        self.assertEqual(self.paths("cat > Makefile <<EOF"), [])
        self.assertEqual(self.paths("cat .nvmrc >> Makefile"), [".nvmrc"])

    def test_input_redirect_is_a_read(self):
        self.assertEqual(self.paths("wc -l < Makefile"), ["Makefile"])

    def test_env_assignment_prefix_is_skipped(self):
        self.assertEqual(self.paths("LANG=C cat Makefile"), ["Makefile"])


if __name__ == "__main__":
    unittest.main()
