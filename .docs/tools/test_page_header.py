#!/usr/bin/env python3
"""Tests for the page header that stage_site.py adds: meta line, strip, See also, breadcrumb, TOC removal."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage_site as ss  # noqa: E402

BODY = "# Title\n\nWords " * 5 + "\n"


class Meta(unittest.TestCase):
    def test_meta_line_and_chips(self):
        out = ss.render_meta("a/p.md", BODY, {"level": "beginner", "type": ["guide", "concept"], "tags": ["gpu", "hpc"]}, "2026-11-13")
        self.assertIn("Beginner · Guide · 1 min read · Updated 13 Nov 2026", out)
        self.assertIn('class="chip" href="#/.docs/generated/explore/tags/gpu"', out)

    def test_note_type_and_missing_fields_are_left_out(self):
        out = ss.render_meta("a/p.md", BODY, {"type": "note"}, None)
        self.assertIn(">1 min read<", out)
        self.assertNotIn("Note", out)
        self.assertNotIn("tag-chips", out)

    def test_root_docs_get_nothing(self):
        self.assertEqual(ss.render_meta("SPEC.md", BODY, {}, None), "")


class Related(unittest.TestCase):
    block = {"prerequisites": [{"title": f"P{n}", "path": f"p{n}.md"} for n in range(3)],
             "required_by": [{"title": "N", "path": "n.md"}],
             "related": [{"title": "R", "path": "r.md"}]}

    def test_top_strip_is_capped_and_has_no_see_also(self):
        out = ss.render_related(self.block)
        self.assertIn("P0", out)
        self.assertIn("P1", out)
        self.assertNotIn("P2", out)
        self.assertNotIn("See also", out)

    def test_see_also_goes_last_with_summary(self):
        out = ss.render_see_also(self.block, {"r.md": "About R."})
        self.assertIn("- [R](/r.md) — About R.", out)
        text = ss.put_related("# T\n\nBody.\n", "", "", out)
        self.assertTrue(text.rstrip().endswith("</div>"))
        self.assertLess(text.index("Body."), text.index("See also"))


class Placement(unittest.TestCase):
    def test_breadcrumb_above_title_strip_below(self):
        t = ss.put_related("# T\n\nBody.\n", "STRIP\n", "CRUMBS\n")
        self.assertLess(t.index("CRUMBS"), t.index("# T"))
        self.assertLess(t.index("# T"), t.index("STRIP"))
        self.assertLess(t.index("STRIP"), t.index("Body."))


class Toc(unittest.TestCase):
    PAGE = "# T\n\nIntro.\n\n## Table of Contents\n- [A](#a)\n  - [B](#b)\n\n---\n\n## A\n\ntext\n\n## B\n\ntext\n"

    def test_removed_with_its_rule(self):
        out = ss.drop_toc("a/p.md", self.PAGE)
        self.assertNotIn("Table of Contents", out)
        self.assertNotIn("---", out)
        self.assertIn("## A", out)
        self.assertIn("Intro.", out)

    def test_folder_readme_keeps_its_list(self):
        self.assertEqual(ss.drop_toc("a/README.md", self.PAGE), self.PAGE)

    def test_prose_under_heading_is_kept(self):
        page = self.PAGE.replace("- [A](#a)", "Some prose here.\n- [A](#a)")
        self.assertEqual(ss.drop_toc("a/p.md", page), page)

    def test_heading_in_code_fence_is_ignored(self):
        page = "# T\n\n```\n## Table of Contents\n```\n\n## A\n\n## B\n\n## C\n"
        self.assertEqual(ss.drop_toc("a/p.md", page), page)


class BareList(unittest.TestCase):
    PAGE = "# T\n\nIntro.\n\n- [A](#a)\n- [B](#b)\n- [C](#c)\n- [D](#d)\n\n## A\n\ntext\n\n## B\n\n## C\n\n## D\n"

    def test_anchor_only_list_before_first_section_is_removed(self):
        out = ss.drop_toc("a/p.md", self.PAGE)
        self.assertNotIn("(#a)", out)
        self.assertIn("Intro.", out)
        self.assertIn("## A", out)

    def test_ordinary_link_list_is_kept(self):
        page = self.PAGE.replace("(#a)", "(/x.md)")
        self.assertEqual(ss.drop_toc("a/p.md", page), page)

    def test_short_list_is_kept(self):
        page = self.PAGE.replace("- [D](#d)\n", "")
        self.assertEqual(ss.drop_toc("a/p.md", page), page)


class Breadcrumb(unittest.TestCase):
    def test_names_come_from_folder_readmes(self):
        root = tempfile.mkdtemp()
        os.makedirs(os.path.join(root, "fields/sched"))
        for rel, h in (("fields/README.md", "# Fields\n"), ("fields/sched/README.md", "# Fields - Schedulers - Overview\n")):
            with open(os.path.join(root, rel), "w") as f:
                f.write(h)
        out = ss.render_breadcrumb("fields/sched/page.md", root)
        self.assertIn('<a href="#/fields/">Fields</a> / <a href="#/fields/sched/">Schedulers</a>', out)
        self.assertEqual(ss.render_breadcrumb("page.md", root), "")


if __name__ == "__main__":
    unittest.main()
