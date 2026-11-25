#!/usr/bin/env python3
"""Tests for generate_index.folder_title / path_names: learning paths are named after their series."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_index as gi  # noqa: E402


def make(files):
    root = tempfile.mkdtemp()
    for rel, text in files.items():
        os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
        with open(os.path.join(root, rel), "w", encoding="utf-8") as f:
            f.write(text)
    return root


class FolderTitle(unittest.TestCase):
    def test_overview_suffix_dropped(self):
        r = make({"a/README.md": "# Fields - Smoke Tests - Overview\n"})
        self.assertEqual(gi.folder_title(r, "a"), "Smoke Tests")

    def test_text_after_last_hyphen(self):
        r = make({"a/README.md": "# Fields - Schedulers\n"})
        self.assertEqual(gi.folder_title(r, "a"), "Schedulers")

    def test_sidebar_group_wins(self):
        r = make({"a/README.md": "---\nsidebar_group: Short Name\n---\n\n# Long - Heading\n"})
        self.assertEqual(gi.folder_title(r, "a"), "Short Name")

    def test_missing_readme(self):
        self.assertEqual(gi.folder_title(make({"x.md": "x"}), "nope"), "")


class PathNames(unittest.TestCase):
    def test_shared_name_gets_first_title(self):
        r = make({"a/README.md": "# Same\n", "b/README.md": "# Same\n"})
        objs = {"p": {"path": "a/p.md", "title": "P"}, "q": {"path": "b/q.md", "title": "Q"}}
        self.assertEqual(gi.path_names(objs, [["p"], ["q"]], {}, r), ["Same (from P)", "Same (from Q)"])


if __name__ == "__main__":
    unittest.main()
