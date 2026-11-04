#!/usr/bin/env python3
"""Tests for check_pins.py (the parsing only; no network). Run: python3 .docs/tools/test_check_pins.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_pins import PAIR_RE, ROOT, TAG_RE, pins, sri_tag  # noqa: E402


class Pins(unittest.TestCase):
    def test_finds_scoped_and_plain_packages(self):
        html = ('<script src="//cdn.jsdelivr.net/npm/docsify@5.0.0/dist/docsify.min.js"></script>'
                '<link href="https://cdn.jsdelivr.net/npm/@scope/pkg@1.2.3/x.css">')
        self.assertEqual(pins(html), {"docsify": {"5.0.0"}, "@scope/pkg": {"1.2.3"}})

    def test_unpinned_address_has_empty_version(self):
        self.assertEqual(pins('<script src="//cdn.jsdelivr.net/npm/mermaid/dist/m.js">'), {"mermaid": {""}})

    def test_ignores_other_hosts(self):
        self.assertEqual(pins('<script src="https://example.com/npm/x@1.0.0/a.js">'), {})


class Integrity(unittest.TestCase):
    def test_sri_tag_adds_and_replaces(self):
        tag = '<script src="//cdn.jsdelivr.net/npm/x@1.0.0/a.js"></script>'[:-9]
        self.assertEqual(sri_tag(tag, "", "sha384-A"),
                         '<script src="//cdn.jsdelivr.net/npm/x@1.0.0/a.js" integrity="sha384-A" crossorigin="anonymous">')
        old = '<link href="//cdn.jsdelivr.net/npm/x@1.0.0/a.css" integrity="sha384-old" crossorigin="anonymous" />'
        self.assertEqual(sri_tag(old, "", "sha384-B"),
                         '<link href="//cdn.jsdelivr.net/npm/x@1.0.0/a.css" integrity="sha384-B" crossorigin="anonymous"/>')

    def test_every_cdn_file_has_a_hash(self):
        """Offline: each CDN tag in index.html and each pair in .docs/*.js carries a sha384 hash."""
        docs = os.path.join(ROOT, ".docs")
        files = [os.path.join(ROOT, "index.html")] + [os.path.join(docs, n) for n in os.listdir(docs) if n.endswith(".js")]
        seen = 0
        for path in files:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for m in TAG_RE.finditer(text):
                seen += 1
                self.assertRegex(m.group(0), r'integrity="sha384-[^"]+" crossorigin="anonymous"', m.group(1))
            for m in PAIR_RE.finditer(text):
                seen += 1
                self.assertTrue(m.group(2).startswith("sha384-"), m.group(1))
        self.assertGreater(seen, 5)


if __name__ == "__main__":
    unittest.main()
