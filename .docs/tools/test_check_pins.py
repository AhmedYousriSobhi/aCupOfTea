#!/usr/bin/env python3
"""Tests for check_pins.py (the parsing only; no network). Run: python3 .docs/tools/test_check_pins.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_pins import pins  # noqa: E402


class Pins(unittest.TestCase):
    def test_finds_scoped_and_plain_packages(self):
        html = ('<script src="//cdn.jsdelivr.net/npm/docsify@5.0.0/dist/docsify.min.js"></script>'
                '<link href="https://cdn.jsdelivr.net/npm/@scope/pkg@1.2.3/x.css">')
        self.assertEqual(pins(html), {"docsify": {"5.0.0"}, "@scope/pkg": {"1.2.3"}})

    def test_unpinned_address_has_empty_version(self):
        self.assertEqual(pins('<script src="//cdn.jsdelivr.net/npm/mermaid/dist/m.js">'), {"mermaid": {""}})

    def test_ignores_other_hosts(self):
        self.assertEqual(pins('<script src="https://example.com/npm/x@1.0.0/a.js">'), {})


if __name__ == "__main__":
    unittest.main()
