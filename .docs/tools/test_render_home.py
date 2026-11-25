#!/usr/bin/env python3
"""Tests for stage_site.render_home: the deployed homepage built from README.md."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage_site as ss  # noqa: E402

README = """# aCupOfTea
# AI Tea Lounge: Sipping Knowledge in AI Domains
![logo](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/1/abc-def)

> **Knowledge, served in short sips.** Short pages.

## Menu

| Section | What |
|---|---|
| [Fields](/fields/README.md) | Things |
| [Journal](/journal/README.md) | Notes |
"""
PAGES = ["fields/a.md", "fields/b.md", "fields/README.md", "fields/x/c.md", "README.md"]


class Home(unittest.TestCase):
    def setUp(self):
        self.out = ss.render_home(README, PAGES)

    def test_one_h1_and_tagline(self):
        self.assertEqual(self.out.count("\n# "), 0)
        self.assertTrue(self.out.startswith("# aCupOfTea\n\n*AI Tea Lounge"))

    def test_logo_is_local(self):
        self.assertIn("(.docs/icons/logo.png)", self.out)
        self.assertNotIn("github.com/AhmedYousriSobhi/aCupOfTea/assets", self.out)

    def test_counts_exclude_readmes_and_skip_empty_folders(self):
        self.assertIn("[Fields](/fields/README.md) <small>3 pages</small> |", self.out)
        self.assertIn("| [Journal](/journal/README.md) |", self.out)

    def test_search_button_after_quote(self):
        self.assertLess(self.out.index("Short pages."), self.out.index("home-search"))

    def test_page_without_the_expected_shape_is_left_alone(self):
        self.assertEqual(ss.render_home("# Other\n\ntext\n", []), "# Other\n\ntext\n")


if __name__ == "__main__":
    unittest.main()
