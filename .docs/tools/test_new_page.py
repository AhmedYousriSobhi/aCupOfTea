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

    def test_new_subject_and_tag_can_be_confirmed_by_option(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers", "--domains", "devops",
                    "--new-domain", "devops=Running software on clusters", "--tags", "fresh-tag",
                    "--new-tag", "fresh-tag=Fresh Tag")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("domains: [devops]", r.stdout)
        self.assertIn("tags: [fresh-tag]", r.stdout)
        self.assertIn("New subjects for taxonomy.yaml: devops", r.stdout)

    def test_missing_folder_needs_create_folder_with_yes(self):
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers/brand-new-sub")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no folder created", r.stderr)
        r = dry_run("--title", "A Quick Look", "--folder", "fields/schedulers/brand-new-sub", "--create-folder")
        self.assertEqual(r.returncode, 0, r.stderr)

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


class Guards(unittest.TestCase):
    """New-tag typo check, any index table, a README for a new folder, --update."""

    def run_main(self, root, *argv, typed=None):
        import contextlib
        import io
        from unittest import mock
        out, code = io.StringIO(), 0
        patches = [mock.patch.object(new_page, "ROOT", root), mock.patch.object(new_page, "regenerate_navigation", lambda: None),
                   mock.patch("sys.argv", ["new_page.py", *argv]), contextlib.redirect_stdout(out)]
        if typed is not None:
            it = iter(typed)
            patches += [mock.patch("builtins.input", lambda prompt="": next(it)), mock.patch.object(new_page.sys.stdin, "isatty", lambda: True),
                        mock.patch.object(new_page, "complete_with", lambda o: None)]
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            try:
                new_page.main()
            except SystemExit as e:
                code = e.code
        return code, out.getvalue()

    def test_new_tag_that_looks_like_a_known_one_is_flagged(self):
        import contextlib
        import io
        ask = new_page.Asker(True)
        args = type("A", (), {"tags": "kubernates"})()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            tags, new = new_page.choose_tags(args, ask, "Intro", {"kubernetes": "Kubernetes", "gpu": "GPU"})
        self.assertIn('looks like "kubernetes"', out.getvalue())

    def test_short_form_is_matched_to_a_title_word_and_can_be_accepted(self):
        import contextlib
        import io
        from unittest import mock
        ask = new_page.Asker(False)
        ask.interactive = True
        answers = iter(["", "y"])      # "Use that instead?" -> y
        args = type("A", (), {"tags": "k8s"})()
        with mock.patch("builtins.input", lambda prompt="": next(answers)), contextlib.redirect_stdout(io.StringIO()):
            tags, new = new_page.choose_tags(args, ask, "Kubernetes in Five Nouns", {"gpu": "GPU", "kubernetes": "Kubernetes"})
        self.assertEqual(tags, ["kubernetes"])
        self.assertEqual(new, {})

    def test_any_table_whose_rows_start_with_a_link_is_the_index(self):
        lines = ["# K\n", "\n", "| Page | What it covers | Time |\n", "| --- | --- | --- |\n",
                 "| [alpha](/k/alpha.md) | A | 5 min |\n"]
        self.assertTrue(new_page.add_table_row(lines, "beta", "/k/beta.md", "About beta."))
        self.assertEqual(lines[-1], "| [beta](/k/beta.md) | About beta. | |\n")
        self.assertFalse(new_page.add_table_row(["# no table\n"], "x", "/x.md", "d"))

    def test_new_folder_gets_a_readme_and_a_row_in_the_parent(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "area", "sub"))
            with open(os.path.join(root, "area", "README.md"), "w", encoding="utf-8") as fh:
                fh.write("# Area\n\n| Directory | Description |\n|---|---|\n| [other](/area/other/README.md) | O |\n")
            old, new_page.ROOT = new_page.ROOT, root
            try:
                msgs = new_page.create_folder_readme("area/sub", "area/sub/page.md", "A Page", "About it.")
            finally:
                new_page.ROOT = old
            with open(os.path.join(root, "area", "sub", "README.md"), encoding="utf-8") as fh:
                readme = fh.read()
            with open(os.path.join(root, "area", "README.md"), encoding="utf-8") as fh:
                parent = fh.read()
        self.assertTrue(readme.startswith("# Sub\n"))
        self.assertIn("| [page](/area/sub/page.md) | About it. |", readme)
        self.assertIn("| [sub](/area/sub/README.md) | Sub |", parent)
        self.assertEqual(len(msgs), 2)

    def page(self, root, text):
        os.makedirs(os.path.join(root, "notes"), exist_ok=True)
        with open(os.path.join(root, "notes", "p.md"), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)

    def test_update_changes_only_what_is_given_and_keeps_the_text(self):
        body = "# P\n\nText.\n"
        with tempfile.TemporaryDirectory() as root:
            self.page(root, "---\nid: p\nsidebar_label: Short\nlevel: advanced\ntype: [concept, guide]\ndomains: [security]\n---\n\n" + body)
            code, out = self.run_main(root, "--update", "notes/p.md", "--level", "beginner", "--summary", "New one.", "--yes")
            with open(os.path.join(root, "notes", "p.md"), encoding="utf-8") as fh:
                after = fh.read()
        self.assertFalse(code, out)
        self.assertIn("level: beginner", after)
        self.assertIn("summary: New one.", after)
        self.assertIn("sidebar_label: Short", after)                  # untouched
        self.assertIn("type: [concept, guide]", after)
        self.assertTrue(after.endswith("\n---\n\n" + body))

    def test_update_dash_clears_and_nothing_to_change_says_so(self):
        with tempfile.TemporaryDirectory() as root:
            self.page(root, "---\nid: p\nlevel: advanced\ndomains: [security]\n---\n\n# P\n")
            code, out = self.run_main(root, "--update", "notes/p.md", "--level", "-", "--yes")
            with open(os.path.join(root, "notes", "p.md"), encoding="utf-8") as fh:
                after = fh.read()
            self.assertFalse(code, out)
            self.assertNotIn("level:", after)
            code, out = self.run_main(root, "--update", "notes/p.md", "--level", "", "--yes")
            self.assertIn("Nothing to change", str(code))

    def test_update_refuses_a_page_without_front_matter_and_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            self.page(root, "# P\n")
            code, out = self.run_main(root, "--update", "notes/p.md", "--level", "beginner", "--yes")
            self.assertIn("--adopt", str(code))
            self.page(root, "---\nid: p\n---\n\n# P\n")
            code, out = self.run_main(root, "--update", "notes/p.md", "--level", "beginner", "--dry-run", "--yes")
            self.assertIn("+level: beginner", out)
            with open(os.path.join(root, "notes", "p.md"), encoding="utf-8") as fh:
                self.assertNotIn("level", fh.read())

    def test_update_asks_with_the_current_value_as_default(self):
        with tempfile.TemporaryDirectory() as root:
            self.page(root, "---\nid: p\nlevel: advanced\ntype: note\ndomains: [security]\ntags: [gpu]\n---\n\n# P\n")
            # summary, type, domains, tags, level, prerequisites, related: Enter keeps all but level
            code, out = self.run_main(root, "--update", "notes/p.md", typed=["", "", "", "", "beginner", "", ""])
            with open(os.path.join(root, "notes", "p.md"), encoding="utf-8") as fh:
                after = fh.read()
        self.assertFalse(code, out)
        self.assertIn("level: beginner", after)
        self.assertIn("tags: [gpu]", after)
        self.assertIn("domains: [security]", after)


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
