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


    def test_unknown_tag_can_be_removed(self):
        text = PAGE.replace("tags: [k8s, kubernates, gpu]", "tags: [gpu, technology]")
        with open(os.path.join(pd.ROOT, self.page), "w", encoding="utf-8") as fh:
            fh.write(text)
        i = pd.describe(self.issue(5, "invalid tag 'technology'; not in taxonomy (gpu)", "validate"))
        self.assertIn("tags: [gpu]", i["fixes"][-1]["files"][self.page])
        self.assertIn("kind: technology", i["hint"])


class Extras(Tree):
    def write(self, rel, text):
        full = os.path.join(pd.ROOT, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(text)

    def test_stale_index_is_found_and_regenerated_without_touching_files_first(self):
        import shutil
        shutil.rmtree(os.path.join(pd.ROOT, "fields"))                  # the fixture pages use tags the real taxonomy lacks
        for name in ("taxonomy.yaml", "schema.yaml"):
            shutil.copy(os.path.join(HERE, "..", "metadata", name), os.path.join(pd.ROOT, ".docs", "metadata", name))
        self.write(".docs/generated/objects.json", "{}")
        self.write("notes/a.md", "---\nid: a-page\ntype: note\ndomains: [security]\n---\n\n# A\n\nText.\n")
        found = pd.stale_index_issue(None)
        self.assertEqual(len(found), 1, found)
        self.assertEqual(found[0]["level"], "error")
        self.assertEqual(pd.read_rel(".docs/generated/objects.json"), "{}")            # looking changed nothing
        self.assertFalse(os.path.exists(os.path.join(pd.ROOT, ".docs/generated/domains.json")))
        pd.apply_fix(found[0]["fixes"][0])                                             # the fix runs the generator
        self.assertIn("a-page", pd.read_rel(".docs/generated/objects.json"))
        self.assertEqual(pd.stale_index_issue(None), [])

    def test_a_picture_without_a_description_asks_for_one(self):
        self.write("notes/p.md", "# P\n\nA ![](a.png) and ![image](b.png) and ![ok text](c.png)\n")
        issues = pd.picture_issues({"notes/p.md"})
        self.assertEqual([i["line"] for i in issues], [3, 3])
        fix = issues[1]["fixes"][0]
        self.assertTrue(fix["input"])
        built = fix["build"]("the second one [with brackets]")
        self.assertIn("![](a.png) and ![the second one (with brackets)](b.png)", built["files"]["notes/p.md"])
        self.assertIsNone(fix["build"]("   "))
        pd.apply_fix(fix, "a cup of tea")
        self.assertIn("![a cup of tea](b.png)", pd.read_rel("notes/p.md"))

    def test_swapped_readmes_are_found_and_swapped_back(self):
        self.write("fields/devops/README.md", "# Kubernetes, for People Who Have Other Things to Do\n")
        self.write("fields/devops/kubernetes/README.md", "# DevOps: Where Code Meets the Machines\n")
        found = pd.readme_swap_issues(None)
        self.assertEqual(len(found), 1, found)
        pd.apply_fix(found[0]["fixes"][0])
        self.assertIn("DevOps", pd.read_rel("fields/devops/README.md"))
        self.assertEqual(pd.readme_swap_issues(None), [])

    def test_correct_readmes_are_left_alone(self):
        self.write("fields/devops/README.md", "# DevOps: Where Code Meets the Machines\n")
        self.write("fields/devops/kubernetes/README.md", "# Kubernetes, for People Who Have Other Things to Do\n")
        self.assertEqual(pd.readme_swap_issues(None), [])

    def test_hook_is_installed_once_and_never_over_someone_elses(self):
        import subprocess
        subprocess.run(["git", "init", "-q", pd.ROOT], check=True)
        with contextlib.redirect_stdout(io.StringIO()):
            pd.install_hook()
            pd.install_hook()                                    # again: same hook, fine
        path = pd.hook_path()
        self.assertTrue(os.access(path, os.X_OK))
        self.assertIn("--pre-push", pd.read_rel(os.path.relpath(path, pd.ROOT)))
        with contextlib.redirect_stdout(io.StringIO()):
            pd.uninstall_hook()
        self.assertFalse(os.path.exists(path))
        self.write(os.path.relpath(path, pd.ROOT), "#!/bin/sh\necho mine\n")
        with self.assertRaises(SystemExit):
            pd.install_hook()
        self.assertIn("mine", pd.read_rel(os.path.relpath(path, pd.ROOT)))


class Related(Tree):
    def test_unrelated_subjects_offer_a_taxonomy_fix_and_removals(self):
        tax = ("domains:\n  business:\n    label: B\n    description: b.\n"
               "  security:\n    label: S\n    description: s.\n    related: [business]\n"
               "  statistics:\n    label: St\n    description: t.\n\ntags:\n  gpu:\n    label: GPU\n")
        with open(os.path.join(pd.ROOT, pd.TAXONOMY_REL), "w", encoding="utf-8") as fh:
            fh.write(tax)
        text = PAGE.replace("domains: [systems-and-hpc]", "domains: [business, statistics]")
        with open(os.path.join(pd.ROOT, self.page), "w", encoding="utf-8") as fh:
            fh.write(text)
        i = pd.describe({"tool": "validate", "level": "warning", "path": self.page, "line": 4,
                         "message": "domains 'business' and 'statistics' are not marked as related in taxonomy.yaml; x"})
        self.assertEqual(len(i["fixes"]), 3)
        self.assertIn("    related: [statistics]\n", i["fixes"][0]["files"][pd.TAXONOMY_REL].split("  business:")[1].split("  security:")[0])
        self.assertIn("domains: [business]", i["fixes"][1]["files"][self.page])      # keep only business
        self.assertIn("domains: [statistics]", i["fixes"][2]["files"][self.page])    # keep only statistics

    def test_add_related_extends_an_existing_list_once(self):
        tax = "domains:\n  a:\n    label: A\n    description: x.\n    related: [b]\n  b:\n    label: B\n    description: y.\n  c:\n    label: C\n    description: z.\n"
        once = pd.add_related(tax, "a", "c")
        self.assertIn("    related: [b, c]\n", once)
        self.assertEqual(pd.add_related(once, "a", "c"), once)


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
        got = pd.parse("validate", lines)
        self.assertTrue(pd.in_scope(got[0]["path"], {"fields/x"}))      # not hidden by the scope


class Grouping(unittest.TestCase):
    def test_alike_problems_share_a_group(self):
        g = pd.group_of
        self.assertEqual(g({"message": "no summary (one line shown in search and Explore)"}),
                         g({"message": "no front matter; create pages with this script"}))
        self.assertEqual(g({"message": "empty section(s): Data Augmentation; fill or remove them"}),
                         g({"message": "3 outline note(s) from the template are still there"}))
        self.assertEqual(g({"message": "picture without a description: ![image](a.png)"}),
                         g({"message": "2 picture(s) without a description (lines 1, 2)"}))
        self.assertNotEqual(g({"message": "no summary (x)"}), g({"message": "relative link(s) break on the site"}))

    def test_unknown_messages_group_by_their_shape(self):
        g = pd.group_of
        self.assertEqual(g({"message": "page 'a' has 3 odd things: x"}), g({"message": "page 'b' has 9 odd things: y"}))

    def test_metadata_and_unfinished_groups_carry_one_hint_for_the_group(self):
        for msg in ("no summary (one line shown in search and Explore)", "empty section(s): A; fill or remove them"):
            i = {"tool": "page", "level": "todo", "path": "a.md", "line": 1, "message": msg}
            with mock.patch.object(pd, "run_tool", return_value=""), mock.patch.object(pd, "pages_in", return_value=["a.md"]), \
                    mock.patch.object(pd, "readme_swap_issues", return_value=[]), mock.patch.object(pd, "stale_index_issue", return_value=[]), \
                    mock.patch.object(pd, "page_todos", return_value=[i]):
                found = pd.page_issues(None)
            self.assertEqual(found[0]["group_hint"], pd.GROUP_HINTS[found[0]["group"]])

    def test_list_is_sorted_group_by_group(self):
        with mock.patch.object(pd, "run_tool", return_value=""), \
                mock.patch.object(pd, "pages_in", return_value=["a.md", "b.md"]), \
                mock.patch.object(pd, "readme_swap_issues", return_value=[]), \
                mock.patch.object(pd, "stale_index_issue", return_value=[]), \
                mock.patch.object(pd, "page_todos", side_effect=lambda rel: [
                    {"tool": "page", "level": "todo", "path": rel, "line": 1, "message": "no summary (x)"},
                    {"tool": "page", "level": "todo", "path": rel, "line": 1, "message": "no level (y)"},
                    {"tool": "page", "level": "todo", "path": rel, "line": 1, "message": "no # title heading"}]):
            found = pd.page_issues(None)
        groups = [i["group"] for i in found]
        self.assertEqual(len(found), 6)
        self.assertEqual(groups[:4], [groups[0]] * 4)           # both pages' metadata items sit together
        self.assertEqual(groups[4], groups[5])                  # then the title heading ones
        self.assertEqual([i["path"] for i in found[:4]], ["a.md", "a.md", "b.md", "b.md"])


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
