#!/usr/bin/env python3
"""Tests for page_gui.py: the local server's guards and its API, run on a throwaway tree.

Standard library only. Run: python3 .docs/tools/test_page_gui.py
"""
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import new_page  # noqa: E402
import page_doctor  # noqa: E402
import page_gui  # noqa: E402

REAL_TAXONOMY = new_page.TAXONOMY


class Api(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        os.makedirs(os.path.join(root, ".docs", "metadata"))
        with open(REAL_TAXONOMY, encoding="utf-8") as src, \
                open(os.path.join(root, ".docs", "metadata", "taxonomy.yaml"), "w", encoding="utf-8") as dst:
            dst.write(src.read())
        os.makedirs(os.path.join(root, "notes"))
        with open(os.path.join(root, "notes", "README.md"), "w", encoding="utf-8") as fh:
            fh.write("# Notes\n\n## Contents\n\n| File | Description |\n|---|---|\n| [a](/notes/a.md) | A |\n")
        with open(os.path.join(root, "notes", "a.md"), "w", encoding="utf-8") as fh:
            fh.write("---\nid: a-page\ntype: note\n---\n\n# A Page\n\nText.\n")
        with open(os.path.join(root, "notes", "hand-made.md"), "w", encoding="utf-8") as fh:
            fh.write("# Hand Made\n\nSome text.\n")
        self.patches = [mock.patch.object(new_page, "ROOT", root), mock.patch.object(page_doctor, "ROOT", root),
                        mock.patch.object(new_page, "TAXONOMY", os.path.join(root, ".docs", "metadata", "taxonomy.yaml")),
                        mock.patch.object(new_page, "regenerate_navigation", lambda: None)]
        for p in self.patches:
            p.start()
        self.httpd = page_gui.make_server()
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def call(self, path, body=None, token=True, host=None):
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, path),
                                     data=None if body is None else json.dumps(body).encode(),
                                     headers={"X-Token": self.httpd.token} if token else {})
        if host:
            req.add_header("Host", host)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def json(self, path, body=None):
        status, data = self.call(path, body)
        self.assertEqual(status, 200, data)
        return json.loads(data)

    # ---- guards
    def test_page_needs_the_token(self):
        self.assertEqual(self.call("/", token=False)[0], 403)
        status, html = self.call("/?t=" + self.httpd.token, token=False)
        self.assertEqual(status, 200)
        self.assertIn(b"aCupOfTea page form", html)

    def test_api_needs_the_token_and_a_local_host(self):
        self.assertEqual(self.call("/api/options", token=False)[0], 403)
        self.assertEqual(self.call("/api/options", host="evil.example:%d" % self.port)[0], 403)
        self.assertEqual(self.call("/api/create", {}, token=False)[0], 403)

    def test_unknown_route(self):
        self.assertEqual(self.call("/api/nope")[0], 404)

    # ---- options
    def test_options_offer_the_vocabulary_and_suggestions(self):
        o = self.json("/api/options?title=Notes%20about%20pages&folder=notes")
        self.assertIn("notes", o["folders"])
        self.assertIn("concept", [t["key"] for t in o["types"]])
        self.assertIn("systems-and-hpc", [d["key"] for d in o["domains"]])
        self.assertEqual(o["limits"], {"types": 2, "domains": 2, "tags": 5})
        self.assertEqual(o["default_type"], ["note"])                       # what the folder's pages use
        self.assertIn("a-page", [p["id"] for p in o["pages"]])
        self.assertTrue(o["folder_exists"])

    def test_options_report_a_missing_folder(self):
        self.assertFalse(self.json("/api/options?folder=notes/new-one")["folder_exists"])

    # ---- create
    def create(self, **kw):
        body = {"title": "Brand New Idea", "folder": "notes", "types": ["concept", "guide"],
                "domains": ["software-engineering"], "tags": [], "summary": "A short one."}
        body.update(kw)
        return self.json("/api/create", body)

    def test_preview_writes_nothing(self):
        r = self.create(dry_run=True)
        self.assertTrue(r["ok"], r)
        self.assertIn("type: [concept, guide]", r["output"])
        self.assertFalse(os.path.exists(os.path.join(new_page.ROOT, "notes", "brand-new-idea.md")))

    def test_create_writes_the_page_and_the_index_row(self):
        r = self.create()
        self.assertTrue(r["ok"], r)
        with open(os.path.join(new_page.ROOT, "notes", "brand-new-idea.md"), encoding="utf-8") as fh:
            self.assertIn("domains: [software-engineering]", fh.read())
        with open(os.path.join(new_page.ROOT, "notes", "README.md"), encoding="utf-8") as fh:
            self.assertIn("| [brand-new-idea](/notes/brand-new-idea.md) | A short one. |", fh.read())
        self.assertIn("Reading time", r["check"])

    def test_an_error_comes_back_as_text_not_a_crash(self):
        r = self.create(domains=["cooking"])
        self.assertFalse(r["ok"])
        self.assertIn("cooking", r["output"])

    def test_new_folder_needs_the_checkbox(self):
        self.assertFalse(self.create(folder="notes/deeper")["ok"])
        self.assertTrue(self.create(folder="notes/deeper", create_folder=True)["ok"])
        self.assertTrue(os.path.isfile(os.path.join(new_page.ROOT, "notes", "deeper", "brand-new-idea.md")))

    def test_new_subject_and_tag_are_added_to_the_taxonomy(self):
        r = self.create(domains=["devops"], new_domains=[{"key": "devops", "description": "Running software."}],
                        tags=["kubernetes"], new_tags=[{"key": "kubernetes", "label": "Kubernetes"}])
        self.assertTrue(r["ok"], r)
        with open(new_page.TAXONOMY, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("  devops:\n    label: Devops\n    description: Running software.\n", text)
        self.assertIn("  kubernetes:\n    label: Kubernetes\n", text)

    # ---- adopt
    def test_adoptable_lists_what_is_missing(self):
        pages = {p["path"]: p for p in self.json("/api/adoptable")}
        self.assertIn("summary", pages["notes/hand-made.md"]["missing"])
        self.assertEqual(pages["notes/a.md"]["have"], ["type"])

    def test_adopt_keeps_the_text(self):
        r = self.json("/api/adopt", {"page": "notes/hand-made.md", "types": ["note"], "domains": ["security"],
                                     "tags": [], "summary": "Made by hand."})
        self.assertTrue(r["ok"], r)
        with open(os.path.join(new_page.ROOT, "notes", "hand-made.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.endswith("\n# Hand Made\n\nSome text.\n"))
        self.assertIn("summary: Made by hand.", text)

    # ---- problems
    def test_open_refuses_paths_outside_the_repo(self):
        self.assertFalse(self.json("/api/open", {"path": "../../etc/passwd"})["ok"])

    def test_fix_of_a_changed_problem_is_refused(self):
        r = self.json("/api/fix", {"id": "gone.md:1:nothing", "fix": 0, "scope": "all"})
        self.assertFalse(r["ok"])
        self.assertIn("changed", r["output"])


if __name__ == "__main__":
    unittest.main()
