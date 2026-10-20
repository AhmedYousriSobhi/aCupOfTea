#!/usr/bin/env python3
"""Tests for the `order` field: validation, sidebar order, Read next / learning paths.

Usage: python3 .docs/tools/test_page_order.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_index  # noqa: E402
import validate  # noqa: E402

DOCS = os.path.join(os.path.dirname(HERE))
PAGE = "---\nid: {id}\n{extra}---\n\n# {title}\n\nText.\n"


class Repo:
    """A throwaway repo root with the sidebar generator and a series folder."""

    def __init__(self, pages):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, ".docs", "metadata"))
        for f in ("gen_sidebar.sh",):
            shutil.copy(os.path.join(DOCS, f), os.path.join(self.root, ".docs", f))
        for f in ("schema.yaml", "taxonomy.yaml"):
            shutil.copy(os.path.join(DOCS, "metadata", f), os.path.join(self.root, ".docs", "metadata", f))
        os.makedirs(os.path.join(self.root, "series"))
        with open(os.path.join(self.root, "series", "README.md"), "w") as f:
            f.write("# Series\n")
        for name, (extra, title) in pages.items():
            with open(os.path.join(self.root, "series", name + ".md"), "w") as f:
                f.write(PAGE.format(id=name, extra=extra, title=title))

    def sidebar(self):
        subprocess.run(["bash", "gen_sidebar.sh"], cwd=os.path.join(self.root, ".docs"), check=True, capture_output=True)
        lines = open(os.path.join(self.root, ".docs", "_sidebar.md")).read().splitlines()
        return [l.split("]")[0].split("[")[-1].strip("*") for l in lines if "series/" in l]

    def __del__(self):
        shutil.rmtree(self.root, ignore_errors=True)


class OrderTests(unittest.TestCase):
    def test_sidebar_follows_order_then_alphabet(self):
        r = Repo({"zeta": ("order: 1\n", "Zeta"), "alpha": ("", "Alpha"), "mid": ("order: 2\n", "Mid"),
                  "beta": ("", "Beta")})
        self.assertEqual(r.sidebar(), ["Series", "Zeta", "Mid", "Alpha", "Beta"])

    def test_without_order_stays_alphabetical(self):
        r = Repo({"b": ("", "B page"), "a": ("", "A page")})
        self.assertEqual(r.sidebar(), ["Series", "A page", "B page"])

    def test_duplicate_order_is_an_error(self):
        r = Repo({"a": ("order: 1\n", "A"), "b": ("order: 1\n", "B")})
        rep, _, _ = validate.run(r.root)
        self.assertTrue(any("duplicate order 1" in m for _, _, m in rep.errors))

    def test_bad_order_values_are_errors(self):
        for bad in ("0", "-1", "two", "true", "1.5"):
            r = Repo({"a": ("order: %s\n" % bad, "A")})
            rep, _, _ = validate.run(r.root)
            self.assertTrue(any("order must be" in m for _, _, m in rep.errors), bad)

    def test_prerequisite_after_page_warns(self):
        r = Repo({"a": ("order: 1\nrelations:\n  prerequisites: [b]\n", "A"), "b": ("order: 2\n", "B")})
        rep, _, _ = validate.run(r.root)
        self.assertFalse(rep.errors)
        self.assertTrue(any("before its prerequisite" in m for _, _, m in rep.warnings))

    def test_prerequisite_first_is_clean(self):
        r = Repo({"a": ("order: 2\nrelations:\n  prerequisites: [b]\n", "A"), "b": ("order: 1\n", "B")})
        rep, _, _ = validate.run(r.root)
        self.assertFalse(rep.errors or rep.warnings)

    def test_read_next_and_paths_use_order(self):
        objs = {i: {"id": i, "title": t, "level": "", "order": o, "path": i + ".md",
                    "relations": {"prerequisites": ["root"] if i != "root" else [], "related": []}}
                for i, t, o in (("root", "Root", 1), ("z", "Zed", 2), ("a", "Aye", 3))}
        rels = generate_index.build_relationships(objs)
        block = generate_index.build_related(objs, rels)["root.md"]
        self.assertEqual([x["id"] for x in block["required_by"]], ["z", "a"])
        self.assertEqual(generate_index.learning_paths(objs), [["root", "z", "a"]])


if __name__ == "__main__":
    unittest.main()
