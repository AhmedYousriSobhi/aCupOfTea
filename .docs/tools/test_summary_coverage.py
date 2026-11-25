#!/usr/bin/env python3
"""Tests for the summary health check: a summary is optional but recommended, so it is counted, never an error.

Usage: python3 .docs/tools/test_summary_coverage.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import validate  # noqa: E402

DOCS = os.path.dirname(HERE)

PAGES = {
    "topic/README.md": "# Topic\n\n## Contents\n\n| File | Description |\n|---|---|\n| [a](/topic/a.md) | A |\n",
    "topic/with-summary.md": "---\nsummary: One line about it.\n---\n\n# With summary\n\nText.\n",
    "topic/front-matter-only.md": "---\ntype: note\n---\n\n# No summary here\n\nText.\n",
    "topic/legacy.md": "# Legacy page\n\nNo front matter at all.\n",
    "topic-page/README.md": "# A README that is itself a topic\n\nNo Contents list, so it is a page.\n",
}


def make_repo(pages):
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, ".docs", "metadata"))
    for f in ("schema.yaml", "taxonomy.yaml"):
        shutil.copy(os.path.join(DOCS, "metadata", f), os.path.join(root, ".docs", "metadata", f))
    for rel, text in pages.items():
        os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
        with open(os.path.join(root, rel), "w") as f:
            f.write(text)
    return root


class SummaryCoverageTests(unittest.TestCase):
    def setUp(self):
        self.root = make_repo(PAGES)
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_counts_content_pages_and_skips_folder_indexes(self):
        rep, _, _ = validate.run(self.root)
        self.assertEqual(rep.summary_total, 4)   # every page but topic/README.md (a folder index)
        self.assertEqual(sorted(rep.summary_missing),
                         ["topic-page/README.md", "topic/front-matter-only.md", "topic/legacy.md"])

    def test_missing_summary_is_not_an_error_or_a_warning(self):
        rep, _, _ = validate.run(self.root)
        self.assertEqual(rep.errors, [])
        self.assertEqual(rep.warnings, [])

    def test_coverage_line(self):
        rep, _, _ = validate.run(self.root)
        self.assertIn("summary coverage: 1 of 4 content pages (25%)", validate.coverage_line(rep))
        self.assertIn("optional but recommended", validate.coverage_line(rep))

    def test_command_line_never_fails_on_missing_summaries(self):
        script = os.path.join(HERE, "validate.py")
        done = subprocess.run([sys.executable, script, "--root", self.root, "--list-missing-summaries"],
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("no summary: topic/legacy.md", done.stdout)
        self.assertNotIn("no summary: topic/README.md", done.stdout)
        only = subprocess.run([sys.executable, script, "--root", self.root, "--summary-coverage"],
                              capture_output=True, text=True)
        self.assertEqual(only.returncode, 0)
        self.assertEqual(len(only.stdout.strip().splitlines()), 1)

    def test_empty_repo_counts_as_full_coverage(self):
        empty = make_repo({})
        self.addCleanup(shutil.rmtree, empty, ignore_errors=True)
        rep, _, _ = validate.run(empty)
        self.assertIn("(100%)", validate.coverage_line(rep))


if __name__ == "__main__":
    unittest.main()
