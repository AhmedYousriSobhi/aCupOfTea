#!/usr/bin/env python3
"""Tests for page_doctor.py: parsing the checks, suggestions, fixes and the editor command.

Standard library only. Run: python3 .docs/tools/test_page_doctor.py
"""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import new_page  # noqa: E402
import page_doctor as pd  # noqa: E402

TAXONOMY = """types:
  concept: x
domains:
  systems-and-hpc:
    label: S
tags:
  gpu:
    label: GPU
    kind: technology
  k8s:
    label: K8s
  kubernates:
    label: Kubernates

folder_defaults:
  x:
    - y
"""
PAGE = """---
id: k8s-intro
type: concept
domains: [systems-and-hpc]
tags: [k8s, kubernates, gpu]
---

# Kubernetes in Five Nouns

See [the readme](kubernetes/README.md) and [sched](../schedulers/) and [gone](missing-page.md).
"""


class Tree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        for rel, text in {".docs/metadata/taxonomy.yaml": TAXONOMY,
                          "fields/devops/kubernetes/kubernetes-in-five-nouns.md": PAGE,
                          "fields/devops/kubernetes/README.md": "# K\n",
                          "fields/schedulers/README.md": "# S\n"}.items():
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                fh.write(text)
        self.page = "fields/devops/kubernetes/kubernetes-in-five-nouns.md"
        self.patches = [mock.patch.object(pd, "ROOT", root), mock.patch.object(new_page, "ROOT", root),
                        mock.patch.object(new_page, "TAXONOMY", os.path.join(root, pd.TAXONOMY_REL))]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def issue(self, line, message, tool="check_links", level="error"):
        return {"tool": tool, "level": level, "path": self.page, "line": line, "message": message}


class Fixes(Tree):
    def test_relative_link_found_by_name_is_not_marked_safe(self):
        i = pd.describe(self.issue(10, "kubernetes/README.md: relative link breaks on the site; write it root-absolute"))
        fix = i["fixes"][0]
        self.assertFalse(fix["safe"])
        self.assertIn("(/fields/devops/kubernetes/README.md)", fix["files"][self.page])
        self.assertIn("[sched](../schedulers/)", fix["files"][self.page])   # other links untouched

    def test_relative_link_that_resolves_is_safe(self):
        with open(os.path.join(pd.ROOT, "fields/devops/kubernetes/notes.md"), "w", encoding="utf-8") as fh:
            fh.write("# N\n")
        text = PAGE.replace("(kubernetes/README.md)", "(notes.md)")
        with open(os.path.join(pd.ROOT, self.page), "w", encoding="utf-8") as fh:
            fh.write(text)
        fix = pd.describe(self.issue(10, "notes.md: relative link breaks on the site; write it root-absolute"))["fixes"][0]
        self.assertTrue(fix["safe"])
        self.assertIn("(/fields/devops/kubernetes/notes.md)", fix["files"][self.page])

    def test_folder_link_keeps_its_slash(self):
        fix = pd.describe(self.issue(10, "../schedulers/: relative link breaks on the site; write it root-absolute"))["fixes"][0]
        self.assertIn("[sched](/fields/schedulers/)", fix["files"][self.page])

    def test_missing_target_without_a_match_has_no_fix(self):
        self.assertEqual(pd.describe(self.issue(10, "missing-page.md: target does not exist"))["fixes"], [])

    def test_tag_short_form_and_typo_are_merged_into_the_title_word(self):
        i = pd.describe(self.issue(5, "tag 'k8s' is used by only one page and is not marked kind: technology",
                                   "validate", "warning"))
        first = i["fixes"][0]
        self.assertIn("tags: [kubernetes, kubernates, gpu]", first["files"][self.page])
        tax = first["files"][pd.TAXONOMY_REL]
        self.assertIn("  kubernetes:\n    label: Kubernetes\n    kind: technology\n", tax)
        self.assertNotIn("  k8s:", tax)                       # no page uses it any more
        self.assertIn("  kubernates:", tax)                   # still on this page
        self.assertIn("mark it kind: technology", i["fixes"][1]["label"])

    def test_second_tag_collapses_into_the_first(self):
        i = pd.describe(self.issue(5, "tag 'kubernates' is used by only one page and is not marked kind: technology",
                                   "validate", "warning"))
        self.assertIn("tags: [k8s, kubernetes, gpu]", i["fixes"][0]["files"][self.page])

    def test_mark_technology_only_touches_the_taxonomy(self):
        fix = pd.describe(self.issue(5, "tag 'k8s' is used by only one page and is not marked kind: technology",
                                     "validate", "warning"))["fixes"][1]
        self.assertEqual(list(fix["files"]), [pd.TAXONOMY_REL])
        self.assertIn("  k8s:\n    label: K8s\n    kind: technology\n  kubernates:", fix["files"][pd.TAXONOMY_REL])

    def test_apply_writes_and_diff_shows_it(self):
        fix = pd.describe(self.issue(10, "../schedulers/: relative link breaks on the site; write it root-absolute"))["fixes"][0]
        self.assertIn("+See [the readme](kubernetes/README.md) and [sched](/fields/schedulers/)", pd.diff_of(fix))
        pd.apply_fix(fix)
        self.assertIn("[sched](/fields/schedulers/)", pd.read_rel(self.page))

    def test_unknown_domain_gets_the_closest_known_one(self):
        i = pd.describe(self.issue(4, "invalid domain 'hpc'; not in taxonomy (systems-and-hpc)", "validate"))
        self.assertEqual(i["fixes"], [])      # 'hpc' alone is in the page? no: it is not listed there
        text = PAGE.replace("domains: [systems-and-hpc]", "domains: [hpc]")
        with open(os.path.join(pd.ROOT, self.page), "w", encoding="utf-8") as fh:
            fh.write(text)
        i = pd.describe(self.issue(4, "invalid domain 'hpc'; not in taxonomy (systems-and-hpc)", "validate"))
        self.assertIn("domains: [systems-and-hpc]", i["fixes"][0]["files"][self.page])


class Pure(unittest.TestCase):
    def test_numeronym_and_typo(self):
        self.assertEqual(pd.suggest_word("k8s", [["explained", "kubernetes"]]), "kubernetes")
        self.assertEqual(pd.suggest_word("kubernates", [["kubernetes"]]), "kubernetes")
        self.assertEqual(pd.suggest_word("gpu", [["kubernetes"]]), "")

    def test_parse_both_formats(self):
        got = pd.parse("x", ["a/b.md:7: warning: tag 'k8s' is used",
                             "a/c.md: warning: 3 picture(s) without a description (lines 18, 107, ...)",
                             "checked 160 pages"])
        self.assertEqual([(g["path"], g["line"], g["level"]) for g in got],
                         [("a/b.md", 7, "warning"), ("a/c.md", 18, "warning")])

    def test_replace_in_list_needs_a_one_line_list(self):
        text = "---\ntags: [a, b]\n---\n\n# T\ntags: [a]\n"
        self.assertEqual(pd.replace_in_list(text, "tags", "a", "c"), "---\ntags: [c, b]\n---\n\n# T\ntags: [a]\n")
        self.assertIsNone(pd.replace_in_list("---\ntags:\n  - a\n---\n", "tags", "a", "c"))

    def test_editor_command_per_editor(self):
        e = lambda spec: pd.editor_command("/p/x.md", 7, {"EDITOR": spec})
        self.assertEqual(e("code"), (["code", "--goto", "/p/x.md:7"], False))
        self.assertEqual(e("vim"), (["vim", "+7", "/p/x.md"], True))
        self.assertEqual(e("nano -w"), (["nano", "-w", "+7", "/p/x.md"], True))
        self.assertEqual(e("gedit"), (["gedit", "/p/x.md"], True))

    def test_a_crashing_check_is_reported_not_swallowed(self):
        fake = mock.Mock(stdout="", stderr="Traceback (most recent call last):\n  x\nTypeError: boom\n")
        with mock.patch.object(pd.subprocess, "run", return_value=fake):
            lines = pd.run_tool("validate.py")
        self.assertIn("crashed (TypeError: boom)", lines[0])


class Interactive(unittest.TestCase):
    def test_open_then_quit(self):
        issue = {"tool": "validate", "level": "warning", "path": "a.md", "line": 3, "message": "m", "hint": "", "fixes": []}
        typed = iter(["1", "q"])
        opened = []
        with mock.patch.object(pd, "page_issues", return_value=[issue]), \
                mock.patch.object(pd, "open_issue", lambda i: opened.append(i["line"]) or False), \
                mock.patch("builtins.input", lambda prompt="": next(typed)), contextlib.redirect_stdout(io.StringIO()):
            code = pd.interactive({"a.md"})
        self.assertEqual((opened, code), ([3], 1))


if __name__ == "__main__":
    unittest.main()
