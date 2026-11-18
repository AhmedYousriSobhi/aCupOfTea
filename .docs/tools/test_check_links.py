#!/usr/bin/env python3
"""Tests for check_links.py (unsafe HTML and the picture-description warning). Run: python3 .docs/tools/test_check_links.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_links import missing_alt, unsafe_html  # noqa: E402


class UnsafeHtml(unittest.TestCase):
    def test_script_is_an_error(self):
        found = list(unsafe_html("text\n<script>alert(1)</script>\n"))
        self.assertEqual([n for n, _, _ in found], [2])
        self.assertIn("<script>", found[0][2])

    def test_allow_comment_on_previous_line(self):
        self.assertEqual(list(unsafe_html("<!-- allow-html -->\n<script src=x></script>\n")), [])

    def test_allow_comment_covers_only_next_line(self):
        text = "<!-- allow-html -->\n<iframe src=x></iframe>\n<script></script>\n"
        self.assertEqual([n for n, _, _ in unsafe_html(text)], [3])

    def test_ignored_in_code(self):
        text = "```html\n<script>alert(1)</script>\n```\nuse `<script>` tags\n"
        self.assertEqual(list(unsafe_html(text)), [])

    def test_handler_and_javascript_link(self):
        text = '<img src=x onerror="alert(1)">\n[x](javascript:alert(1))\n'
        self.assertEqual([n for n, _, _ in unsafe_html(text)], [1, 2])


class MissingAlt(unittest.TestCase):
    def test_placeholders_and_file_names_are_counted(self):
        text = ("![](images/a.png)\n"
                "![image](images/b.png) and ![Image](images/c.png)\n"
                "![img](x.png)\n"
                "![image.png](x.png)\n"
                "![Screenshot 2023-01-01 at 10.00.00.png](x.png)\n"
                "![image-1](x.png)\n")
        self.assertEqual(list(missing_alt(text)), [1, 2, 2, 3, 4, 5, 6])

    def test_code_is_ignored(self):
        text = "```md\n![image](x.png)\n```\nwrite `![image](x.png)` like this\n"
        self.assertEqual(list(missing_alt(text)), [])

    def test_real_descriptions_are_not_flagged(self):
        text = ("![ROC curve of the classifier](images/roc.png)\n"
                "![Elbow method for optimal K](images/elbow.png)\n"
                "[![image of a cat sleeping](cat.png)](https://example.com)\n")
        self.assertEqual(list(missing_alt(text)), [])

    def test_image_inside_a_link_is_checked(self):
        self.assertEqual(list(missing_alt("[![image](x.png)](https://example.com)\n")), [1])


if __name__ == "__main__":
    unittest.main()
