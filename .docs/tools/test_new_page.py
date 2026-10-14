#!/usr/bin/env python3
"""Tests for new_page.py: dry-run output, folder ranking and the README index link.

Standard library only. Run: python3 .docs/tools/test_new_page.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import new_page  # noqa: E402

SCRIPT = os.path.join(HERE, "new_page.py")


def dry_run(*args):
    return subprocess.run([sys.executable, "-I", SCRIPT, "--dry-run", "--yes", *args],
                          capture_output=True, text=True)


class DryRun(unittest.TestCase):
    def test_front_matter_has_level_and_prerequisites(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers",
                    "--level", "beginner", "--prerequisites", "sequence-models")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("level: beginner", r.stdout)
        self.assertIn("  prerequisites: [sequence-models]", r.stdout)

    def test_unknown_prerequisite_is_refused(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers",
                    "--prerequisites", "no-such-page")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no-such-page", r.stderr)

    def test_hyphenated_title_note(self):
        r = dry_run("--title", "Deep Learning - Tips", "--folder", "fields/schedulers")
        self.assertIn("the sidebar shows the full title", r.stdout)

    def test_folder_ranking(self):
        folders = new_page.scan()
        self.assertEqual(new_page.suggest_folders("Slurm job arrays", folders)[0], "fields/schedulers")


class IndexLink(unittest.TestCase):
    def link(self, readme):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "f"))
            path = os.path.join(root, "f", "README.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(readme)
            old, new_page.ROOT = new_page.ROOT, root
            try:
                msg = new_page.link_in_readme("f", "f/beta.md", "Beta Page", "About beta.")
            finally:
                new_page.ROOT = old
            with open(path, encoding="utf-8") as fh:
                return msg, fh.read()

    def test_file_table_keeps_alphabetical_order(self):
        msg, out = self.link("# F\n\n| File | Description |\n|---|---|\n| [alpha](/f/alpha.md) | A |\n| [gamma](/f/gamma.md) | G |\n")
        self.assertTrue(msg.startswith("Linked"))
        rows = [l for l in out.splitlines() if l.startswith("| [")]
        self.assertEqual([r.split("]")[0] for r in rows], ["| [alpha", "| [beta", "| [gamma"])
        self.assertIn("| [beta](/f/beta.md) | About beta. |", out)

    def test_directory_file_header(self):
        msg, out = self.link("# F\n\n| Directory/File | Description |\n|---|---|\n| [alpha](/f/alpha.md) | A |\n")
        self.assertTrue(msg.startswith("Linked"))
        self.assertIn("| [beta](/f/beta.md) | About beta. |", out)

    def test_bullet_list_gets_a_bullet(self):
        msg, out = self.link("# F\n\n## What is Covered?\n- [A](/f/a.md)\n- [B](/f/b.md)")
        self.assertTrue(msg.startswith("Linked"))
        self.assertTrue(out.rstrip().endswith("- [Beta Page](/f/beta.md)"), out)

    def test_no_index_prints_the_line(self):
        msg, out = self.link("# F\n\nJust text.\n")
        self.assertIn("yourself", msg)
        self.assertEqual(out, "# F\n\nJust text.\n")


if __name__ == "__main__":
    unittest.main()
