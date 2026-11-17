#!/usr/bin/env python3
"""Tests for build_search_index.py: clean labels and authored summaries."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_search_index as bsi  # noqa: E402

TEXT = "# Page\n\nA long enough opening paragraph that would otherwise become the description of the page, so it needs to be long, really quite long, longer than the one hundred and twenty characters of the cut.\n"


class Labels(unittest.TestCase):
    def test_bold_is_stripped(self):
        self.assertEqual(bsi.clean_label("**Preemption and Signals**"), "Preemption and Signals")

    def test_page_entry_has_plain_label(self):
        e = bsi.index_page({"label": "**Folder**", "path": "a/README.md"}, TEXT)
        self.assertEqual(e["label"], "Folder")


class Descriptions(unittest.TestCase):
    def test_summary_wins(self):
        e = bsi.index_page({"label": "P", "path": "p.md"}, TEXT, "The authored **summary**.")
        self.assertEqual(e["desc"], "The authored summary.")

    def test_fallback_is_first_text(self):
        e = bsi.index_page({"label": "P", "path": "p.md"}, TEXT)
        self.assertTrue(e["desc"].startswith("A long enough opening"))
        self.assertEqual(len(e["desc"]), 120)


if __name__ == "__main__":
    unittest.main()
