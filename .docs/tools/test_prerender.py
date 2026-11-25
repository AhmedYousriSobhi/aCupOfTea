#!/usr/bin/env python3
"""Tests for prerender.py: Markdown to static HTML for the share pages."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prerender as pr  # noqa: E402
import share_pages as sp  # noqa: E402


def r(text, page="a/b.md", depth=2):
    return pr.render_body(text, page, depth)


class Blocks(unittest.TestCase):
    def test_headings_paragraphs_and_inline(self):
        h = r("## Head\n\nSome **bold**, *it* and `co<de>` text\nsecond line.\n")
        self.assertIn("<h2>Head</h2>", h)
        self.assertIn("<strong>bold</strong>", h)
        self.assertIn("<em>it</em>", h)
        self.assertIn("<code>co&lt;de&gt;</code>", h)
        self.assertIn("text second line.", h)

    def test_lists_nested(self):
        h = r("- one\n  - inner\n- two\n\n1. a\n2. b\n")
        self.assertIn("<ul><li>one<ul><li>inner</li></ul></li><li>two</li></ul>", h)
        self.assertIn("<ol><li>a</li><li>b</li></ol>", h)

    def test_code_fence_is_escaped(self):
        h = r("```python\nx = '<b>' & 1\n```\n")
        self.assertIn('<pre><code class="language-python">x = &#x27;&lt;b&gt;&#x27; &amp; 1</code></pre>', h)

    def test_table_and_quote(self):
        h = r("| A | B |\n|---|---|\n| 1 | 2 |\n\n> quoted *x*\n")
        self.assertIn("<th>A</th>", h)
        self.assertIn("<td>2</td>", h)
        self.assertIn("<blockquote><p>quoted <em>x</em></p></blockquote>", h)

    def test_raw_html_and_math_are_dropped(self):
        h = r("<script>alert(1)</script>\n\n$$\nx^2\n$$\n\nText.\n")
        self.assertNotIn("script", h)
        self.assertNotIn("x^2", h)
        self.assertIn("<p>Text.</p>", h)

    def test_text_is_escaped(self):
        self.assertIn("&lt;img onerror=x&gt;", r("a <img onerror=x> b\n"))

    def test_front_matter_is_removed(self):
        self.assertNotIn("title:", r("---\ntitle: T\n---\n\nBody.\n"))


class Links(unittest.TestCase):
    def test_root_absolute_page_goes_to_share_address(self):
        self.assertIn('href="../../x/y/"', r("[t](/x/y.md)"))
        self.assertIn('href="../../x/"', r("[t](/x/README.md)"))

    def test_relative_page_and_image(self):
        self.assertIn('href="../../a/c/"', r("[t](c.md)"))
        self.assertIn('src="../../a/images/p.png"', r("![d](images/p.png)"))

    def test_code_file_keeps_extension_and_anchor_only_is_dropped(self):
        self.assertIn('href="../../x/s.py"', r("[t](/x/s.py)"))
        self.assertNotIn("<a ", r("[t](#section)"))

    def test_external_ok_and_javascript_dropped(self):
        self.assertIn('href="https://e.org/a?b=1"', r("[t](https://e.org/a?b=1)"))
        self.assertNotIn("<a ", r("[t](javascript:alert(1))"))

    def test_lab_link_with_ignore_title_and_embed_marker(self):
        out = r("[Bayes lab](/x/labs/bayes.html#embed ':ignore')")
        self.assertIn('href="../../x/labs/bayes.html"', out)
        self.assertNotIn("ignore", out)
        self.assertNotIn("embed", out)

    def test_home_link(self):
        self.assertIn('href="../../"', r("[t](/README.md)"))


class Page(unittest.TestCase):
    def test_share_page_holds_text_and_script_redirect(self):
        with tempfile.TemporaryDirectory() as out:
            sp.write_share_pages(out, {"a/b.md": "---\ntitle: T\nsummary: S.\n---\n\n# T\n\n## Part\n\nBody text.\n"}, "https://e.org/")
            page = open(os.path.join(out, "a/b/index.html"), encoding="utf-8").read()
            self.assertEqual(page.count("<h1>"), 1)
            self.assertIn("<h2>Part</h2>", page)
            self.assertIn("Body text.", page)
            self.assertIn('<script src="../../.docs/prerender-redirect.js" data-target="../../#/a/b">', page)
            self.assertIn('rel="canonical"', page)


if __name__ == "__main__":
    unittest.main()
