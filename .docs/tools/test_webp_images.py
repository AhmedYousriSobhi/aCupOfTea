#!/usr/bin/env python3
"""Tests for webp_images.py: lossless copies, rewritten image links, sizes."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import webp_images as wi  # noqa: E402

try:
    from PIL import Image
except ImportError:  # the tests need Pillow, like the deploy
    Image = None


@unittest.skipIf(Image is None, "Pillow not installed")
class Webp(unittest.TestCase):
    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp())
        os.makedirs(os.path.join(self.root, "notes", "images"))
        # a flat 40x20 picture compresses well as WebP
        Image.new("RGB", (40, 20), (200, 30, 30)).save(os.path.join(self.root, "notes", "images", "a.png"))
        Image.new("RGB", (30, 30), (1, 2, 3)).save(os.path.join(self.root, "notes", "images", "b.jpg"))

    def page(self, text):
        p = os.path.join(self.root, "notes", "p.md")
        with open(p, "w") as f:
            f.write(text)
        return p

    def run_tree(self, text):
        p = self.page(text)
        summary = wi.convert_tree(self.root)
        return open(p).read(), summary

    def test_png_gets_a_lossless_copy_and_the_page_points_at_it(self):
        out, summary = self.run_tree("# P\n\n![red box](images/a.png)\n")
        self.assertTrue(os.path.isfile(os.path.join(self.root, "notes", "images", "a.png")))   # fallback stays
        self.assertIn("![red box](images/a.webp ':size=40x20')", out)
        self.assertIn("1 image links in 1 pages", summary)
        self.assertEqual(Image.open(os.path.join(self.root, "notes", "images", "a.webp")).convert("RGB").getpixel((3, 3)), (200, 30, 30))

    def test_jpeg_keeps_its_name_and_gets_a_size(self):
        out, _ = self.run_tree("![j](images/b.jpg)\n")
        self.assertIn("![j](images/b.jpg ':size=30x30')", out)

    def test_remote_titled_and_fenced_images_are_left_alone(self):
        text = '![r](https://x.org/a.png)\n![t](images/a.png "A title")\n\n```\n![c](images/a.png)\n```\n'
        out, _ = self.run_tree(text)
        self.assertEqual(out, text)

    def test_a_missing_file_is_left_alone(self):
        out, _ = self.run_tree("![m](images/missing.png)\n")
        self.assertEqual(out, "![m](images/missing.png)\n")

    def test_html_img_points_at_the_copy(self):
        out, _ = self.run_tree('<img src="images/a.png" alt="x">\n')
        self.assertIn('src="images/a.webp"', out)

    def test_path_outside_the_site_is_not_followed(self):
        out, _ = self.run_tree("![o](../../outside.png)\n")
        self.assertEqual(out, "![o](../../outside.png)\n")


if __name__ == "__main__":
    unittest.main()
