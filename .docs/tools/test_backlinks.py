#!/usr/bin/env python3
"""Tests for backlinks.py."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backlinks as bl  # noqa: E402

TEXTS = {
    "README.md": "# Home\n\n[a](/notes/a.md)\n",
    "notes/README.md": "# Notes\n\n## Contents\n\n| File | Description |\n| --- | --- |\n| [a](/notes/a.md) | x |\n",
    "notes/a.md": "# A\n\nSee [b](/notes/b) and [b again](/notes/b.md#part) and [self](/notes/a.md).\n",
    "notes/b.md": "# B\n\nBack to [A](/notes/a.md), a folder [notes](/notes/), `[code](/notes/c.md)`, and ![pic](/notes/a.md)\n\n```\n[fenced](/notes/c.md)\n```\n",
    "notes/c.md": "# C\n\nExternal [x](https://example.org/notes/a.md) and a missing [m](/notes/none.md).\n",
}


class Backlinks(unittest.TestCase):
    def setUp(self):
        self.found = bl.build(TEXTS)

    def test_a_page_counts_once_per_target(self):
        self.assertEqual(self.found["notes/b.md"], ["notes/a.md"])

    def test_indexes_and_self_links_do_not_count(self):
        self.assertEqual(self.found["notes/a.md"], ["notes/b.md"])  # not the root README or the folder index
        self.assertNotIn("notes/README.md", self.found.get("notes/a.md", []))

    def test_a_folder_address_means_its_readme(self):
        # notes/README.md is an index; only b links to it, and a link to a folder resolves to its README
        self.assertEqual(self.found["notes/README.md"], ["notes/b.md"])

    def test_code_images_external_and_missing_do_not_count(self):
        self.assertNotIn("notes/c.md", self.found)

    def test_render(self):
        titles = {"notes/b.md": "B page", "notes/a.md": "A page"}
        out = bl.render(["notes/b.md", "notes/a.md"], titles, {"notes/a.md": "About A."})
        self.assertIn("**Mentioned in**", out)
        self.assertTrue(out.index("A page") < out.index("B page"))
        self.assertIn("[A page](/notes/a.md) — About A.", out)
        self.assertEqual(bl.render([], {}, {}), "")

    def test_long_lists_are_cut(self):
        srcs = ["p%02d.md" % i for i in range(11)]
        out = bl.render(srcs, {}, {}, limit=8)
        self.assertIn("and 3 more", out)


if __name__ == "__main__":
    unittest.main()
