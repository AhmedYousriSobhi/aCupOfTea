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


FENCED = "# Page\n\nIntro text that is not code.\n\n```python\nimport torch\nx = torch.zeros(3)\n```\n\nAfter.\n"


class Split(unittest.TestCase):
    def test_code_is_its_own_field_and_not_in_the_text(self):
        e = bsi.index_page({"label": "P", "path": "p.md"}, FENCED)
        self.assertIn("torch.zeros(3)", e["code"])
        self.assertFalse(any("torch" in s["body"] for s in e["secs"]))

    def test_metadata_goes_to_the_title_entry(self):
        meta = {"type": "guide", "level": "beginner", "reading_time_min": 4, "domains": ["a"], "tags": ["t"]}
        e = bsi.index_page({"label": "P", "path": "p.md"}, FENCED, "", meta)
        self.assertEqual((e["type"], e["level"], e["min"], e["domains"], e["tags"]), ("guide", "beginner", 4, ["a"], ["t"]))

    def test_build_writes_two_files(self):
        import json
        import tempfile
        site = tempfile.mkdtemp()
        os.makedirs(os.path.join(site, ".docs"))
        with open(os.path.join(site, ".docs/_sidebar.md"), "w") as f:
            f.write("- [P](/p.md)\n")
        with open(os.path.join(site, "p.md"), "w") as f:
            f.write(FENCED)
        bsi.build(site)
        titles = json.load(open(os.path.join(site, ".docs/index-titles.json")))
        bodies = json.load(open(os.path.join(site, ".docs/index-body.json")))
        self.assertNotIn("secs", titles[0])
        self.assertNotIn("code", titles[0])
        self.assertIn("torch", bodies["p.md"]["code"])
        self.assertTrue(bodies["p.md"]["secs"])


if __name__ == "__main__":
    unittest.main()
