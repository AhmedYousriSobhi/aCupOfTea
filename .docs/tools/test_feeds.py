#!/usr/bin/env python3
"""Tests for feeds.py: sitemap, Atom feed, robots.txt."""
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feeds  # noqa: E402

BASE = "https://x.org/site/"
SRC = {"a/one.md": "# One\n\nThe first page has a long enough first paragraph to count as a summary.\n",
       "a/README.md": "# A folder\n\nAbout it, in a paragraph long enough to be used.\n"}


class Feeds(unittest.TestCase):
    def test_sitemap_lists_home_and_pages_at_share_addresses(self):
        root = ET.fromstring(feeds.sitemap(BASE, ["a/one.md", "a/README.md", "README.md"], {"a/one.md": "2026-01-02"}))
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [u.find("s:loc", ns).text for u in root.findall("s:url", ns)]
        self.assertEqual(locs, [BASE, BASE + "a/one/", BASE + "a/"])
        self.assertEqual(root.findall("s:url", ns)[1].find("s:lastmod", ns).text, "2026-01-02")
        self.assertIsNone(root.findall("s:url", ns)[0].find("s:lastmod", ns))

    def test_atom_is_valid_xml_with_escaped_text(self):
        xml = feeds.atom(BASE, [("2026-03-04", "a/one.md", "Q&A <one>", "Tom & \"Jerry\"")])
        root = ET.fromstring(xml)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entry = root.find("a:entry", ns)
        self.assertEqual(entry.find("a:title", ns).text, "Q&A <one>")
        self.assertEqual(entry.find("a:link", ns).get("href"), BASE + "a/one/")
        self.assertEqual(root.find("a:updated", ns).text, "2026-03-04T00:00:00Z")

    def test_empty_feed_is_still_valid(self):
        ET.fromstring(feeds.atom(BASE, []))

    def test_write_all_writes_three_files(self):
        out = tempfile.mkdtemp()
        n = feeds.write_all(out, "https://x.org/site", ["a/one.md"], {}, [("2026-03-04", "a/one.md")], SRC)
        self.assertEqual(n, (1, 1))
        for name in ("sitemap.xml", "feed.xml", "robots.txt"):
            self.assertTrue(os.path.isfile(os.path.join(out, name)), name)
        self.assertIn("Sitemap: https://x.org/site/sitemap.xml", open(os.path.join(out, "robots.txt")).read())
        self.assertIn("<title>One</title>", open(os.path.join(out, "feed.xml")).read())


if __name__ == "__main__":
    unittest.main()
