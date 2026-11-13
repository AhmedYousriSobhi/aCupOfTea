#!/usr/bin/env python3
"""Tests for share_pages.py: page metadata, share-page paths and the written HTML."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import share_pages as sp  # noqa: E402

BASE = "https://example.org/site/"


class PageMeta(unittest.TestCase):
    def test_front_matter_wins(self):
        t = "---\ntitle: Own title\nsummary: One line summary.\n---\n\n# Heading\n\nBody text here.\n"
        self.assertEqual(sp.page_meta(t), ("Own title", "One line summary."))

    def test_h1_and_first_paragraph(self):
        t = "# Sequence **Models**\n\n> a quote\n\nHow [models](/a.md) handle `ordered` data.\nSecond line.\n\nLater.\n"
        self.assertEqual(sp.page_meta(t), ("Sequence Models", "How models handle ordered data. Second line."))

    def test_skips_code_tables_and_images(self):
        t = "# T\n\n```\nnot this\n```\n\n| a | b |\n|---|---|\n\n![x](i.png)\n\nReal text.\n"
        self.assertEqual(sp.page_meta(t)[1], "Real text.")

    def test_long_description_is_cut_at_a_word(self):
        d = sp.page_meta("# T\n\n" + "word " * 100)[1]
        self.assertTrue(d.endswith("…") and len(d) <= sp.MAX_DESC + 1)

    def test_broken_front_matter_does_not_crash(self):
        self.assertEqual(sp.page_meta("---\ntitle: [oops\n---\n# H\n\nText.\n"), ("H", "Text."))


class Paths(unittest.TestCase):
    def test_dirs_and_routes(self):
        self.assertIsNone(sp.share_dir("README.md"))
        self.assertEqual(sp.share_dir("a/b.md"), "a/b")
        self.assertEqual(sp.share_dir("a/README.md"), "a")
        self.assertEqual(sp.route("a/b.md"), "/a/b")
        self.assertEqual(sp.route("a/README.md"), "/a/")


class Write(unittest.TestCase):
    def test_writes_pages_and_skips_root_readme(self):
        with tempfile.TemporaryDirectory() as out:
            n = sp.write_share_pages(out, {
                "README.md": "# Home\n\nHi.\n",
                "a/b.md": "# B & \"C\"\n\nText \"quoted\".\n",
                "a/README.md": "# A\n\nFolder.\n",
            }, BASE)
            self.assertEqual(n, 2)
            self.assertFalse(os.path.exists(os.path.join(out, "index.html")))
            page = open(os.path.join(out, "a/b/index.html"), encoding="utf-8").read()
            self.assertIn('content="0; url=../../#/a/b"', page)
            self.assertIn('og:url" content="https://example.org/site/a/b/"', page)
            self.assertIn("B &amp; &quot;C&quot;", page)
            self.assertNotIn("<script", page)
            folder = open(os.path.join(out, "a/index.html"), encoding="utf-8").read()
            self.assertIn('url=../#/a/"', folder)

    def test_readme_wins_over_same_named_page(self):
        with tempfile.TemporaryDirectory() as out:
            sp.write_share_pages(out, {"a.md": "# Page\n\nx\n", "a/README.md": "# Folder\n\ny\n"}, BASE)
            self.assertIn("<title>Folder</title>", open(os.path.join(out, "a/index.html"), encoding="utf-8").read())

    def test_never_overwrites_an_existing_file(self):
        with tempfile.TemporaryDirectory() as out:
            os.makedirs(os.path.join(out, "a/b"))
            with open(os.path.join(out, "a/b/index.html"), "w") as f:
                f.write("mine")
            self.assertEqual(sp.write_share_pages(out, {"a/b.md": "# B\n"}, BASE), 0)
            self.assertEqual(open(os.path.join(out, "a/b/index.html")).read(), "mine")


if __name__ == "__main__":
    unittest.main()
