#!/usr/bin/env python3
"""Tests for new_page.py: dry-run output, folder ranking and the README index link.

Standard library only. Run: python3 .docs/tools/test_new_page.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import new_page  # noqa: E402

SCRIPT = os.path.join(HERE, "new_page.py")


def dry_run(*args):
    return subprocess.run([sys.executable, "-I", SCRIPT, "--dry-run", "--yes", *args],
                          capture_output=True, text=True)


class DryRun(unittest.TestCase):
    def test_front_matter_has_level_and_prerequisites(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers",
                    "--level", "beginner", "--prerequisites", "sequence-models")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("level: beginner", r.stdout)
        self.assertIn("  prerequisites: [sequence-models]", r.stdout)

    def test_unknown_prerequisite_is_refused(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers",
                    "--prerequisites", "no-such-page")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no-such-page", r.stderr)

    def test_hyphenated_title_note(self):
        r = dry_run("--title", "Deep Learning - Tips", "--folder", "fields/schedulers")
        self.assertIn("the sidebar shows the full title", r.stdout)

    def test_type_domains_and_related(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers", "--type", "guide",
                    "--domains", "systems-and-hpc", "--related", "sequence-models")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("type: guide", r.stdout)
        self.assertIn("domains: [systems-and-hpc]", r.stdout)
        self.assertIn("  related: [sequence-models]", r.stdout)

    def test_domains_suggested_from_neighbours(self):
        r = dry_run("--title", "Slurm Job Arrays", "--folder", "fields/schedulers")
        self.assertIn("domains: [systems-and-hpc", r.stdout)

    def test_unknown_domain_is_refused(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers", "--domains", "cooking")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cooking", r.stderr)

    def test_two_types_are_written_as_a_list(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers", "--type", "concept,guide")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("type: [concept, guide]", r.stdout)

    def test_three_types_are_refused(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers", "--type", "concept,guide,note")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("at most 2", r.stderr)

    def test_unknown_domain_suggests_a_known_one(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers", "--domains", "hpc")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("did you mean systems-and-hpc", r.stderr)

    def test_folder_ranking(self):
        folders = new_page.scan()
        self.assertEqual(new_page.suggest_folders("Slurm job arrays", folders)[0], "fields/schedulers")


class Prompts(unittest.TestCase):
    """Typed answers: a bad one is asked again, a new subject can be added."""

    def answers(self, *typed):
        import io
        from unittest import mock
        ask = new_page.Asker(False)
        ask.interactive = True
        it = iter(typed)
        out = io.StringIO()
        patches = [mock.patch("builtins.input", lambda prompt="": next(it)),
                   mock.patch("sys.stdout", out), mock.patch.object(new_page, "complete_with", lambda o: None)]
        return ask, patches

    def run_with(self, patches, fn):
        for p in patches:
            p.start()
        try:
            return fn()
        finally:
            for p in patches:
                p.stop()

    def test_bad_type_is_asked_again(self):
        ask, patches = self.answers("cooking", "concept, guide")
        args = type("A", (), {"type": None})()
        got = self.run_with(patches, lambda: new_page.choose_type(args, ask, "fields/schedulers", new_page.scan()))
        self.assertEqual(got, ["concept", "guide"])

    def test_short_form_and_new_subject(self):
        ask, patches = self.answers("devops, hpc", "y", "Running software on clusters", "")
        args = type("A", (), {"domains": None})()
        domains, new = self.run_with(patches, lambda: new_page.choose_domains(
            args, ask, "fields/schedulers", new_page.scan(), "Kubernetes"))
        self.assertEqual(domains, ["devops", "systems-and-hpc"])
        self.assertEqual(new, {"devops": ("Devops", "Running software on clusters")})

    def test_add_domains_writes_the_taxonomy(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "taxonomy.yaml")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("domains:\n  a:\n    label: A\n    description: x.\n\ntags:\n  t:\n    label: T\n")
            old, new_page.TAXONOMY = new_page.TAXONOMY, path
            try:
                new_page.add_domains({"b": ("B", "y.")})
                self.assertEqual(new_page.load_section("domains"), ["a", "b"])
                self.assertEqual(new_page.load_section("tags"), ["t"])
            finally:
                new_page.TAXONOMY = old


class Adopt(unittest.TestCase):
    """--adopt adds front matter to a hand-written page and leaves its text alone."""
    BODY = "# Hand Made\n\nSome text.\n\n```\n# not a title\n```\n"

    def run_adopt(self, body, *extra):
        import contextlib
        import io
        from unittest import mock
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "notes"))
            page = os.path.join(root, "notes", "hand-made.md")
            with open(page, "wb") as fh:
                fh.write(body.encode("utf-8"))
            with open(os.path.join(root, "notes", "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Notes\n\n## Contents\n\n| File | Description |\n|---|---|\n| [a](/notes/a.md) | A |\n")
            argv = ["new_page.py", "--adopt", "notes/hand-made.md", "--yes", "--type", "concept,guide",
                    "--domains", "software-engineering", "--tags", "", "--prerequisites", "",
                    "--related", "", "--summary", "A short one.", *extra]
            out, code = io.StringIO(), 0
            with mock.patch.object(new_page, "ROOT", root), mock.patch.object(new_page, "regenerate_navigation", lambda: None), \
                    mock.patch("sys.argv", argv), contextlib.redirect_stdout(out):
                try:
                    new_page.main()
                except SystemExit as e:
                    code = e.code
            with open(page, "rb") as fh:
                after = fh.read().decode("utf-8")
            with open(os.path.join(root, "notes", "README.md"), encoding="utf-8") as fh:
                readme = fh.read()
            return code, after, readme, out.getvalue()

    def test_front_matter_added_and_text_unchanged(self):
        code, after, readme, _ = self.run_adopt(self.BODY)
        self.assertFalse(code)
        head, _, rest = after.partition("---\n\n")
        self.assertTrue(head.startswith("---\nid: hand-made\ntitle: Hand Made\n"))
        self.assertIn("type: [concept, guide]", head)
        self.assertEqual(rest, self.BODY)                       # byte for byte
        self.assertIn("| [hand-made](/notes/hand-made.md) | A short one. |", readme)

    def test_crlf_page_gets_crlf_front_matter(self):
        body = self.BODY.replace("\n", "\r\n")
        code, after, _, _ = self.run_adopt(body)
        self.assertFalse(code)
        self.assertTrue(after.endswith("---\r\n\r\n" + body))
        self.assertNotIn("\n", after.replace("\r\n", ""))

    def test_partial_front_matter_is_completed_and_kept(self):
        code, after, _, _ = self.run_adopt("---\nsidebar_label: Short\n---\n\n" + self.BODY)
        self.assertFalse(code)
        head, _, rest = after.partition("\n---\n\n")
        self.assertEqual(head.splitlines()[:4], ["---", "id: hand-made", "sidebar_label: Short", "summary: A short one."])
        self.assertIn("type: [concept, guide]", head)
        self.assertEqual(head.count("sidebar_label"), 1)
        self.assertEqual(rest, self.BODY)

    def test_complete_front_matter_has_nothing_to_add(self):
        body = ("---\nid: x\nsummary: s\ntype: note\ndomains: [security]\ntags: []\nlevel: beginner\n"
                "relations:\n  related: [y]\n---\n\n" + self.BODY)
        code, after, _, _ = self.run_adopt(body)
        self.assertIn("Nothing to add", str(code))
        self.assertEqual(after, body)

    def test_unclosed_front_matter_is_refused(self):
        body = "---\nid: x\n\n" + self.BODY
        code, after, _, _ = self.run_adopt(body)
        self.assertTrue(code)
        self.assertEqual(after, body)

    def test_dry_run_changes_nothing(self):
        code, after, readme, out = self.run_adopt(self.BODY, "--dry-run")
        self.assertFalse(code)
        self.assertEqual(after, self.BODY)
        self.assertNotIn("hand-made", readme)
        self.assertIn("id: hand-made", out)

    def test_page_without_heading_is_refused(self):
        code, after, _, _ = self.run_adopt("just text\n")
        self.assertTrue(code)
        self.assertEqual(after, "just text\n")


class Check(unittest.TestCase):
    def test_reading_time_and_todos(self):
        page = ("---\nid: x\ntitle: X\n---\n\n# X\n\n" + "word " * 450
                + "\n\n## Example\n\n<!-- Code, commands -->\n\n![image](images/a.png)\n\n```\n" + "code " * 900 + "\n```\n")
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "x.md"), "w", encoding="utf-8") as fh:
                fh.write(page)
            old, new_page.ROOT = new_page.ROOT, root
            try:
                import contextlib
                import io
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    todos = new_page.check_page("x.md")
            finally:
                new_page.ROOT = old
        text = out.getvalue()
        self.assertIn("Reading time: 3 min", text)   # 450+ words, code not counted
        self.assertIn("outline note", text)
        self.assertIn("without a description", text)
        self.assertIn("no domains", text)
        self.assertGreaterEqual(todos, 4)


class IndexLink(unittest.TestCase):
    def link(self, readme):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "f"))
            path = os.path.join(root, "f", "README.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(readme)
            old, new_page.ROOT = new_page.ROOT, root
            try:
                msg = new_page.link_in_readme("f", "f/beta.md", "Beta Page", "About beta.")
            finally:
                new_page.ROOT = old
            with open(path, encoding="utf-8") as fh:
                return msg, fh.read()

    def test_file_table_keeps_alphabetical_order(self):
        msg, out = self.link("# F\n\n| File | Description |\n|---|---|\n| [alpha](/f/alpha.md) | A |\n| [gamma](/f/gamma.md) | G |\n")
        self.assertTrue(msg.startswith("Linked"))
        rows = [l for l in out.splitlines() if l.startswith("| [")]
        self.assertEqual([r.split("]")[0] for r in rows], ["| [alpha", "| [beta", "| [gamma"])
        self.assertIn("| [beta](/f/beta.md) | About beta. |", out)

    def test_directory_file_header(self):
        msg, out = self.link("# F\n\n| Directory/File | Description |\n|---|---|\n| [alpha](/f/alpha.md) | A |\n")
        self.assertTrue(msg.startswith("Linked"))
        self.assertIn("| [beta](/f/beta.md) | About beta. |", out)

    def test_bullet_list_gets_a_bullet(self):
        msg, out = self.link("# F\n\n## What is Covered?\n- [A](/f/a.md)\n- [B](/f/b.md)")
        self.assertTrue(msg.startswith("Linked"))
        self.assertTrue(out.rstrip().endswith("- [Beta Page](/f/beta.md)"), out)

    def test_no_index_prints_the_line(self):
        msg, out = self.link("# F\n\nJust text.\n")
        self.assertIn("yourself", msg)
        self.assertEqual(out, "# F\n\nJust text.\n")


if __name__ == "__main__":
    unittest.main()
