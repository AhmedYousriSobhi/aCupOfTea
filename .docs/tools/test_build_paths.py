#!/usr/bin/env python3
"""Tests for generate_index.build_paths: the place of each page in its learning path."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_index as gi  # noqa: E402


def obj(path, prereq=()):
    return {"path": path, "title": path, "level": "", "relations": {"prerequisites": list(prereq), "related": []}}


class BuildPaths(unittest.TestCase):
    def test_position_total_and_next(self):
        objs = {"a": obj("x/a.md"), "b": obj("x/b.md", ["a"]), "c": obj("x/c.md", ["b"])}
        got = gi.build_paths(objs)
        self.assertEqual(got["x/a"], {"pos": 1, "total": 3, "next": {"path": "x/b", "title": "x/b.md"}})
        self.assertEqual(got["x/c"], {"pos": 3, "total": 3, "next": None})

    def test_page_outside_any_path_is_absent(self):
        objs = {"a": obj("x/a.md"), "z": obj("x/z.md")}
        self.assertEqual(gi.build_paths(objs), {})


if __name__ == "__main__":
    unittest.main()
