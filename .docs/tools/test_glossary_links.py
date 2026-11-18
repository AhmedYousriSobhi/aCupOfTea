#!/usr/bin/env python3
"""Tests for glossary_links.py."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glossary_links as gl  # noqa: E402

GLOSSARY = """---
id: glossary
---

# Glossary

Intro with MPI in it.

## MPI

**Message Passing Interface.** The standard. Read more: [x](/a.md).

## GPU

**Graphics Processing Unit.** A processor.

## QoS

**Quality of Service.** Limits.
"""
TERMS = gl.parse(GLOSSARY)


def link(text, page="a/b.md"):
    return gl.link_terms(page, text, TERMS)


class Parse(unittest.TestCase):
    def test_terms_and_tooltips(self):
        self.assertEqual(TERMS, {"MPI": "Message Passing Interface", "GPU": "Graphics Processing Unit", "QoS": "Quality of Service"})


class Link(unittest.TestCase):
    def test_first_use_only_with_a_tooltip(self):
        out, n = link("# T\n\nA GPU job. Another GPU job.\n")
        self.assertEqual(n, 1)
        self.assertEqual(out.count("[GPU]"), 1)
        self.assertIn('[GPU](/references/glossary?id=gpu "Graphics Processing Unit") job. Another GPU job.', out)

    def test_two_terms_in_one_line(self):
        out, n = link("# T\n\nMPI on a GPU.\n")
        self.assertEqual(n, 2)
        self.assertIn('[MPI](/references/glossary?id=mpi', out)
        self.assertIn('[GPU](/references/glossary?id=gpu', out)

    def test_untouched_places(self):
        text = "\n".join(["# GPU notes", "", "## About MPI", "", "`GPU` in code", "[GPU guide](/x.md) and ![GPU](img.png)",
                          "https://example.org/GPU/page", "$GPU$ and <b>GPU</b>", "", "```", "GPU in a fence", "```", "", "    GPU indented",
                          "<div>GPU</div>", "MPI_Send and GPUs and xGPU"])
        out, n = link(text)
        # the heading names GPU, so GPU is never linked on this page; MPI only appears in a heading, in code-like text or HTML
        self.assertEqual(out, text)
        self.assertEqual(n, 0)

    def test_after_a_skipped_use_the_next_plain_use_links(self):
        out, n = link("# T\n\nSee `GPU` first.\n\nThen a GPU.\n")
        self.assertEqual(n, 1)
        self.assertIn("Then a [GPU](", out)
        self.assertIn("`GPU` first", out)

    def test_page_title_naming_the_term_skips_it(self):
        out, n = link("# QoS in practice\n\nQoS limits and a GPU.\n")
        self.assertNotIn("[QoS]", out)
        self.assertIn("[GPU]", out)

    def test_glossary_itself_and_empty_terms(self):
        self.assertEqual(link("A GPU.", page=gl.GLOSSARY), ("A GPU.", 0))
        self.assertEqual(gl.link_terms("a.md", "A GPU.", {}), ("A GPU.", 0))

    def test_tables_indexes_and_inline_definitions_are_skipped(self):
        out, n = link("# T\n\n| A | GPU job |\n| - | - |\nGraphics Processing Unit (GPU) first, then a GPU.\n")
        self.assertEqual(n, 1)
        self.assertIn("Unit (GPU) first, then a [GPU](", out)
        index = "# I\n\n## Contents\n\nA GPU here.\n"
        self.assertEqual(link(index), (index, 0))

    def test_case_sensitive_whole_words(self):
        out, n = link("# T\n\ngpu and GPUs and Gpu.\n")
        self.assertEqual(n, 0)

    def test_crlf_text_keeps_its_line_ends(self):
        out, n = link("# T\r\n\r\nA GPU.\r\n")
        self.assertEqual(n, 1)
        self.assertIn("\r\n", out)


if __name__ == "__main__":
    unittest.main()
