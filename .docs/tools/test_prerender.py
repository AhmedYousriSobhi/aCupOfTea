#!/usr/bin/env python3
"""Tests for prerender.py: a page's Markdown as static HTML for its share page."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prerender as pr  # noqa: E402

PAGES = {"README.md", "a/b.md", "a/c.md", "a/README.md", "x/README.md"}


@unittest.skipUnless(pr.available(), "markdown-it-py is not installed")
class Render(unittest.TestCase):
    def page(self, text, page="a/b.md", up="../../"):
        return pr.body_html(page, text, up, PAGES)

    def test_front_matter_dropped_headings_get_docsify_ids(self):
        out = self.page("---\ntitle: T\nsummary: S\n---\n# My Title\n\n## Sec & Two\n\n## Sec & Two\n")
        self.assertNotIn("summary", out)
        self.assertIn('<h1 id="my-title">My Title</h1>', out)
        self.assertIn('<h2 id="sec--two">', out)
        self.assertIn('<h2 id="sec--two-1">', out)

    def test_page_links_go_to_share_pages(self):
        out = self.page("[c](/a/c.md) [s](/a/c.md?id=part) [f](/a/README.md) [r](./c.md) [h](/README.md) [d](/a/)")
        self.assertIn('href="../../a/c/"', out)
        self.assertIn('href="../../a/c/#part"', out)
        self.assertIn('href="../../a/"', out)
        self.assertIn('href="../../"', out)
        self.assertEqual(out.count('href="../../a/c/"'), 2)

    def test_code_files_and_unknown_pages_go_to_docsify(self):
        out = self.page("[p](/a/run.py) [n](/a/nb.ipynb) [m](/z/missing.md) [r](#/a/c)")
        self.assertIn('href="../../#/a/run.py"', out)
        self.assertIn('href="../../#/a/nb.ipynb"', out)
        self.assertIn('href="../../#/z/missing"', out)
        self.assertIn('href="../../#/a/c"', out)

    def test_external_anchor_and_data_links(self):
        out = self.page("[e](https://x.org/p) [m](mailto:a@b.c) [s](#here) [d](/a/data.csv)")
        for href in ("https://x.org/p", "mailto:a@b.c", "#here", "../../a/data.csv"):
            self.assertIn(f'href="{href}"', out)

    def test_images_resolve_from_the_page_folder(self):
        # a page's share page is one folder deeper than the page; a folder README's is not
        out = self.page("![a](images/p.png ':size=10')\n\n<img src=\"images/q.png\">\n")
        self.assertIn('src="../../a/images/p.png"', out)
        self.assertIn('src="../../a/images/q.png"', out)
        self.assertIn('loading="lazy"', out)
        self.assertNotIn("size=", out)
        out = self.page("![a](images/p.png)", page="x/README.md", up="../")
        self.assertIn('src="../x/images/p.png"', out)

    def test_tables_code_and_escaping(self):
        out = self.page("| a | b |\n|---|---|\n| 1 | 2 |\n\n```python\nx = 1 < 2\n```\n\n~~old~~\n")
        self.assertIn("<table>", out)
        self.assertIn("x = 1 &lt; 2", out)
        self.assertIn("<s>old</s>", out)

    def test_folders_without_a_page_go_to_github(self):
        out = pr.body_html("a/b.md", "[d](/a/data/) [s](/projects/sub) [f](/a/x.csv)", "../../", PAGES,
                           exists=lambda p: p == "a/x.csv")
        self.assertIn(f'href="https://github.com/{pr.REPO}/tree/{pr.BRANCH}/a/data"', out)
        self.assertIn(f'href="https://github.com/{pr.REPO}/tree/{pr.BRANCH}/projects/sub"', out)
        self.assertIn('href="../../a/x.csv"', out)

    def test_links_never_leave_the_site_root(self):
        out = self.page("[up](../../../../etc/passwd)")
        self.assertIn('href="../../../../etc/passwd"', out)  # left as written, not resolved


class Addresses(unittest.TestCase):
    def test_share_address(self):
        self.assertIsNone(pr.share_address("README.md"))
        self.assertEqual(pr.share_address("a/README.md"), "a/")
        self.assertEqual(pr.share_address("a/b.md"), "a/b/")


if __name__ == "__main__":
    unittest.main()
