#!/usr/bin/env python3
"""Tests for stage_site.bundle_scripts: the local scripts before Docsify become one file."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage_site  # noqa: E402

HTML = """<head>
  <!-- a comment with a > sign: ok -->
  <script src="./.docs/theme-toggle.js"></script>
</head>
<body>
  <!-- settings -->
  <script src="./.docs/a.js"></script>
  <script src="./.docs/b.js"></script>
  <!-- lazy -->
  <script src="./.docs/c.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/docsify@5.0.0/dist/docsify.min.js"></script>
  <script src="./.docs/after.js"></script>
</body>
"""


class Bundle(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.out, ".docs"))
        with open(os.path.join(self.out, "index.html"), "w") as f:
            f.write(HTML)
        for n in ("theme-toggle", "a", "b", "c", "after"):
            with open(os.path.join(self.out, ".docs", n + ".js"), "w") as f:
                f.write("window.ran = (window.ran || []).concat(%r);" % n)

    def test_run_before_docsify_is_joined_in_order(self):
        self.assertEqual(stage_site.bundle_scripts(self.out), 3)
        html = open(os.path.join(self.out, "index.html")).read()
        self.assertEqual(html.count('<script src="./.docs/site.js"></script>'), 1)
        self.assertNotIn("a.js", html)
        self.assertIn("theme-toggle.js", html)  # the head script and the one after Docsify stay separate
        self.assertIn("after.js", html)
        js = open(os.path.join(self.out, ".docs", "site.js")).read()
        self.assertTrue(js.index("'a'") < js.index("'b'") < js.index("'c'"))

    def test_each_file_has_its_own_try(self):
        stage_site.bundle_scripts(self.out)
        js = open(os.path.join(self.out, ".docs", "site.js")).read()
        self.assertEqual(js.count("try {"), 3)
        self.assertEqual(js.count("catch (e)"), 3)

    def test_no_run_means_nothing_changes(self):
        with open(os.path.join(self.out, "index.html"), "w") as f:
            f.write("<body></body>")
        self.assertEqual(stage_site.bundle_scripts(self.out), 0)
        self.assertFalse(os.path.exists(os.path.join(self.out, ".docs", "site.js")))


if __name__ == "__main__":
    unittest.main()
