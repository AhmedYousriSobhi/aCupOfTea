#!/usr/bin/env python3
"""Tests for suggest_related.py: the text-similarity scorer and the suggestions built on it.

Usage: python3 .docs/tools/test_suggest_related.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import suggest_related as sr  # noqa: E402

PAGES = {
    "hpc/slurm.md": {"title": "Slurm batch jobs", "domains": ["systems-and-hpc"], "summary": "",
                     "text": "Slurm batch jobs\nSubmit a job script to the cluster scheduler with sbatch.", "first": ""},
    "hpc/mpi.md": {"title": "MPI ranks", "domains": ["systems-and-hpc"], "summary": "",
                   "text": "MPI ranks\nRanks run on cluster nodes and talk through the network.", "first": ""},
    "ml/trees.md": {"title": "Decision trees", "domains": ["machine-learning"], "summary": "",
                    "text": "Decision trees\nA tree splits data by features to predict a label.", "first": ""},
}
DOMAINS = {"systems-and-hpc": {"label": "Systems and HPC", "description": "Clusters and schedulers."},
           "machine-learning": {"label": "Machine Learning", "description": "Learning from data."}}


class StemTests(unittest.TestCase):
    def test_plural_and_suffix_forms_match(self):
        self.assertEqual(sr.tokens("Jobs scheduled"), sr.tokens("job scheduling"))
        self.assertEqual(sr.stem("jobs"), sr.stem("job"))
        self.assertEqual(sr.stem("class"), "class")   # "ss" is not a plural

    def test_stop_words_are_dropped(self):
        self.assertEqual(sr.tokens("the and of"), [])


class ScorerTests(unittest.TestCase):
    def test_identical_text_scores_highest_and_scores_are_repeatable(self):
        corpus = {k: p["text"] for k, p in PAGES.items()}
        a, _ = sr.TfidfScorer(corpus).similarity(corpus["ml/trees.md"])
        b, _ = sr.TfidfScorer(corpus).similarity(corpus["ml/trees.md"])
        self.assertEqual(a, b)
        self.assertEqual(max(a, key=a.get), "ml/trees.md")
        self.assertAlmostEqual(a["ml/trees.md"], 1.0, places=6)

    def test_unknown_words_score_zero(self):
        scores, _ = sr.TfidfScorer({k: p["text"] for k, p in PAGES.items()}).similarity("zzzz qqqq")
        self.assertTrue(all(v == 0 for v in scores.values()))


class SuggestTests(unittest.TestCase):
    def test_a_new_hpc_topic_gets_the_hpc_subject_and_the_slurm_page(self):
        ranking, near = sr.suggest(PAGES, DOMAINS, "Slurm job arrays", "Many similar jobs from one script")
        self.assertEqual(ranking[0][0], "systems-and-hpc")
        self.assertEqual(near[0][0], "hpc/slurm.md")
        self.assertIn("slurm", near[0][2])

    def test_an_unrelated_topic_finds_no_close_page(self):
        _, near = sr.suggest(PAGES, DOMAINS, "Cooking pasta", "Boil water and salt it")
        self.assertEqual(near, [])

    def test_the_page_itself_can_be_left_out(self):
        _, near = sr.suggest(PAGES, DOMAINS, "Slurm batch jobs", "", exclude={"hpc/slurm.md"})
        self.assertNotIn("hpc/slurm.md", [r for r, _, _ in near])


class RepoTests(unittest.TestCase):
    def test_leave_one_out_on_the_real_pages_stays_useful(self):
        pages, domains = sr.load()
        _, hit1, hit3, total = sr.evaluate(pages, domains)
        self.assertGreater(total, 30)
        self.assertGreaterEqual(hit3 / total, 0.85)   # measured 98%: a floor, so a regression shows


if __name__ == "__main__":
    unittest.main()
