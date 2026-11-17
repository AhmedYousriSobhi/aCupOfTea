#!/usr/bin/env python3
"""Tests for pagemodel.py, gen_sidebar.py and gen_navbar.py (the menu rules)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_navbar  # noqa: E402
import gen_sidebar  # noqa: E402
import pagemodel  # noqa: E402


def tree(files):
    root = tempfile.mkdtemp()
    for rel, text in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    return root, os.path.join(root, ".docs")


def menu(files):
    root, docs = tree(files)
    return gen_sidebar.build(root, docs).splitlines()


class Labels(unittest.TestCase):
    def page(self, text, name="a-page.md"):
        root, _ = tree({name: text})
        return pagemodel.Page(os.path.join(root, name))

    def test_after_last_hyphen(self):
        self.assertEqual(self.page("# Fields - Schedulers - Slurm\n").menu_label(), "Slurm")

    def test_sidebar_label_wins_and_yaml_comment_is_ignored(self):
        self.assertEqual(self.page("---\nsidebar_label: Short  # a note\n---\n# Long - Title\n").menu_label(), "Short")

    def test_no_heading_uses_file_name(self):
        self.assertEqual(self.page("text\n", "weird_name-x.md").menu_label(), "Weird Name X")

    def test_group_before_last_hyphen_and_override(self):
        self.assertEqual(self.page("# Fields - A Group - Overview\n").menu_group("a"), "Fields - A Group")
        self.assertEqual(self.page("---\nsidebar_group: Mine\n---\n# X - Y\n").menu_group("a"), "Mine")

    def test_order_must_be_a_whole_number(self):
        self.assertEqual(self.page("---\norder: 3\n---\n# T\n").order, 3)
        self.assertIsNone(self.page("---\norder: soon\n---\n# T\n").order)
        self.assertIsNone(self.page("# T\n").order)


class Menu(unittest.TestCase):
    def test_overview_first_then_order_then_readme_links_then_alphabet(self):
        lines = menu({
            "README.md": "# Home\n",
            "f/README.md": "# Group\n\n- [z](z.md)\n",
            "f/overview.md": "# Overview\n",
            "f/o2.md": "---\norder: 2\n---\n# Two\n",
            "f/o1.md": "---\norder: 1\n---\n# One\n",
            "f/z.md": "# Zed\n",
            "f/a.md": "# Alpha\n",
        })
        labels = [l.split("]")[0].split("[")[-1].strip("*") for l in lines if "f/" in l and "README" not in l]
        self.assertEqual(labels, ["Overview", "One", "Two", "Zed", "Alpha"])

    def test_root_docs_hidden_and_about_group_last(self):
        lines = menu({"README.md": "# H\n", "SPEC.md": "# Spec\n", "CLAUDE.md": "# C\n", "f/p.md": "# P\n"})
        self.assertNotIn("* [Spec](SPEC.md)", lines)
        self.assertEqual(lines[-3], "* **About this site**")
        self.assertFalse(any("CLAUDE" in l for l in lines))

    def test_folder_without_pages_or_hidden_is_skipped(self):
        lines = menu({"README.md": "# H\n", "data/x.csv": "1\n", "f/.h/p.md": "# P\n", "g/p.md": "# P\n"})
        self.assertIn("* **G**", lines)
        self.assertFalse(any("Data" in l or "**F**" in l for l in lines))

    def test_group_heading_links_to_readme_and_nests(self):
        lines = menu({"README.md": "# H\n", "a/README.md": "# A - Group\n", "a/b/README.md": "# B\n", "a/b/p.md": "# P\n"})
        self.assertIn("* [**A**](a/README.md)", lines)
        self.assertIn("  * [**B**](a/b/README.md)", lines)
        self.assertIn("    * [P](a/b/p.md)", lines)


class Navbar(unittest.TestCase):
    def test_categories_from_top_level_folders(self):
        root, _ = tree({"README.md": "x", "my_folder/README.md": "x", "plain/x.md": "x", ".hid/x.md": "x", "_site/x.md": "x"})
        out = gen_navbar.build(root)
        self.assertIn("  * [My Folder](my_folder/README.md)", out)
        self.assertIn("  * [Plain](plain/)", out)
        self.assertNotIn("hid", out)
        self.assertNotIn("_site", out)


if __name__ == "__main__":
    unittest.main()
