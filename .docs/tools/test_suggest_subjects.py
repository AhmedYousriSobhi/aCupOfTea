#!/usr/bin/env python3
"""Tests for suggest_subjects.py: a title and summary get the subject and pages that share its words.

Usage: python3 .docs/tools/test_suggest_subjects.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import suggest_subjects as ss  # noqa: E402

TAXONOMY = {"domains": {
    "schedulers": {"label": "Schedulers", "description": "Batch schedulers such as Slurm: jobs, queues and priorities."},
    "deep-learning": {"label": "Deep Learning", "description": "Neural networks and deep architectures."},
}}
OBJECTS = {
    "slurm-intro": {"title": "Slurm Intro", "summary": "How Slurm queues and runs jobs.", "domains": ["schedulers"], "tags": []},
    "fairshare": {"title": "Fairshare", "summary": "Job priority in a batch queue.", "domains": ["schedulers"], "tags": []},
    "cnn": {"title": "Convolutional Networks", "summary": "Neural networks for images.", "domains": ["deep-learning"], "tags": []},
}


class SuggestTest(unittest.TestCase):
    def test_subject_and_pages_follow_the_words(self):
        out = ss.suggest("Why my Slurm job waits", "Queue priority explained.", OBJECTS, TAXONOMY)
        self.assertEqual(out["subjects"][0][0], "schedulers")
        self.assertIn("slurm-intro", [k for k, _, _ in out["pages"]])
        self.assertNotIn("cnn", [k for k, _, _ in out["pages"]])

    def test_every_suggestion_has_a_reason(self):
        out = ss.suggest("Training a neural network", "", OBJECTS, TAXONOMY)
        self.assertEqual(out["subjects"][0][0], "deep-learning")
        self.assertTrue(all(why for _, _, why in out["subjects"] + out["pages"]))

    def test_no_shared_word_suggests_nothing(self):
        out = ss.suggest("Quantum cooking", "", OBJECTS, TAXONOMY)
        self.assertEqual(out, {"subjects": [], "pages": []})

    def test_skip_id_leaves_a_page_out(self):
        out = ss.suggest("Slurm Intro", "How Slurm queues and runs jobs.", OBJECTS, TAXONOMY, skip_id="slurm-intro")
        self.assertNotIn("slurm-intro", [k for k, _, _ in out["pages"]])


if __name__ == "__main__":
    unittest.main()
