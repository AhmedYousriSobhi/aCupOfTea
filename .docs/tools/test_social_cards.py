#!/usr/bin/env python3
"""Tests for social_cards.py and the card tags of share_pages.py."""
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import share_pages as sp  # noqa: E402
import social_cards as sc  # noqa: E402


@unittest.skipUnless(sc.have_pillow(), "Pillow not installed")
class Cards(unittest.TestCase):
    def test_card_is_a_1200_by_630_png(self):
        data = sc.card_bytes("A title", "A summary.", "Fields · Tests")
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        w, h = struct.unpack(">II", data[16:24])
        self.assertEqual((w, h), (1200, 630))

    def test_very_long_text_and_odd_characters_still_render(self):
        self.assertTrue(sc.card_bytes("word " * 200, "x " * 500, "k"))
        self.assertTrue(sc.card_bytes("Ünïcode → 中文", "", ""))

    def test_share_pages_point_at_the_card(self):
        out = tempfile.mkdtemp()
        n = sp.write_share_pages(out, {"notes/deep/page.md": "# Page\n\nA first paragraph of the page, long enough to be used.\n"}, "https://x.org/")
        self.assertEqual(n, 1)
        self.assertTrue(os.path.isfile(os.path.join(out, "notes/deep/page/card.png")))
        html = open(os.path.join(out, "notes/deep/page/index.html")).read()
        self.assertIn('og:image" content="https://x.org/notes/deep/page/card.png"', html)
        self.assertIn("summary_large_image", html)
        self.assertTrue(html.endswith("</html>\n"))


class NoCard(unittest.TestCase):
    def test_without_a_card_the_icon_is_used(self):
        html = sp.render("a/b.md", "B", "d", "https://x.org/", card=False)
        self.assertIn(".docs/icons/icon-512.png", html)
        self.assertIn('twitter:card" content="summary"', html)

    def test_kicker_names_the_folders(self):
        self.assertEqual(sp.kicker("fields/deep-learning/concepts/x", "fields/deep-learning/concepts/x.md"), "Fields · Deep Learning")


if __name__ == "__main__":
    unittest.main()
