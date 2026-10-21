#!/usr/bin/env python3
"""Suggest subjects and related pages for a new topic from the text of the existing pages.

Prototype for #198. The score is TF-IDF cosine similarity (pure Python, no new dependency) between the
title and summary you give and (a) each subject's description plus its pages, (b) every existing page.
The scoring sits behind `TfidfScorer.similarity`, so another backend (embeddings) can replace it later.

Usage:
  python3 .docs/tools/suggest_related.py --title "Slurm Job Arrays" --summary "Run many similar jobs with one script"
  python3 .docs/tools/suggest_related.py --evaluate        # leave-one-out check against the subjects already chosen
"""
import argparse
import math
import os
import re
import sys
from collections import Counter

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import list_pages, read_text, split_front_matter, submodule_paths  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
STOP = set("""a about above after again all also an and any are as at be because been before being below between both but by
can could did do does doing down during each few for from further had has have having he her here hers him his how i if in
into is it its itself just me more most my no nor not now of off on once only or other our out over own same she should so
some such than that the their them then there these they this those through to too under until up very was we were what
when where which while who whom why will with would you your use used using one two get make makes""".split())
WORD = re.compile(r"[a-z][a-z0-9+#]{1,}")
FENCE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.DOTALL | re.MULTILINE)
NEIGHBOURS = 5          # how many nearest pages vote for a subject
RELATED_MIN = 0.08      # a page closer than this counts as related; if none is, the topic is new here
LINK = re.compile(r"\]\([^)]*\)")


def stem(w):
    """A light plural/suffix strip, enough to match 'jobs' with 'job'; not a real stemmer."""
    for suffix, repl in (("ies", "y"), ("sses", "ss"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
        if w.endswith(suffix) and len(w) - len(suffix) >= 3 and not (suffix == "s" and w.endswith("ss")):
            return w[: -len(suffix)] + repl
    return w


def tokens(text):
    return [stem(w) for w in WORD.findall(text.lower()) if w not in STOP]


def page_text(body):
    """Prose of a page: code fences, link targets, images and formulas removed."""
    body = FENCE.sub(" ", body)
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", body)
    body = LINK.sub("]", body)
    return re.sub(r"\$\$.*?\$\$", " ", body)


class TfidfScorer:
    """TF-IDF cosine similarity over a fixed corpus {doc_id: text}. Swap this class for another backend if needed."""

    def __init__(self, corpus):
        self.counts = {k: Counter(tokens(t)) for k, t in corpus.items()}
        df = Counter(w for c in self.counts.values() for w in c)
        n = len(corpus)
        self.idf = {w: math.log((1 + n) / (1 + d)) + 1 for w, d in df.items()}
        self.vecs = {k: self._vec(c) for k, c in self.counts.items()}

    def _vec(self, counts):
        v = {w: (1 + math.log(c)) * self.idf[w] for w, c in counts.items() if w in self.idf}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {w: x / norm for w, x in v.items()}

    def query_vec(self, text):
        return self._vec(Counter(tokens(text)))

    @staticmethod
    def cosine(a, b):
        if len(a) > len(b):
            a, b = b, a
        return sum(x * b.get(w, 0.0) for w, x in a.items())

    def similarity(self, text, exclude=()):
        """{doc_id: cosine} of `text` against every document, plus the shared terms that explain each score."""
        q = self.query_vec(text)
        return {k: self.cosine(q, v) for k, v in self.vecs.items() if k not in exclude}, q

    def shared_terms(self, q, doc_id, top=3):
        v = self.vecs[doc_id]
        shared = sorted(((x * v[w], w) for w, x in q.items() if w in v), reverse=True)
        return [w for _, w in shared[:top]]


def load(root=ROOT):
    """Pages {rel: {title, domains, summary, text}} and the taxonomy's domains {key: {label, description}}."""
    with open(os.path.join(root, ".docs", "metadata", "taxonomy.yaml"), encoding="utf-8") as f:
        tax = yaml.safe_load(f)
    pages = {}
    for rel in list_pages(root, set(submodule_paths(root))):
        text = read_text(root, rel)
        split = split_front_matter(text)
        fm, body = {}, text
        if split:
            try:
                fm = yaml.safe_load(split[0]) or {}
            except yaml.YAMLError:
                fm = {}
            body = text[text.index("\n---", 3) + 4:] if text.startswith("---") else text
        if os.path.basename(rel) == "README.md" and re.search(r"^## Contents\s*$", body, re.M):
            continue   # a folder index is navigation, not a topic
        h1 = re.search(r"^# (.+)$", body, re.M)
        title = str(fm.get("title") or (h1.group(1) if h1 else os.path.basename(rel)[:-3]))
        doms = fm.get("domains") if isinstance(fm.get("domains"), list) else []
        if not doms:   # folders like fields/tabular-data carry default subjects (taxonomy.yaml folder_defaults)
            doms = next((d for f, d in (tax.get("folder_defaults") or {}).items() if rel.startswith(f + "/")), [])
        first = next((p.strip() for p in re.split(r"\n\s*\n", page_text(body)) if p.strip() and not p.lstrip().startswith("#")), "")
        pages[rel] = {"title": title, "domains": doms, "summary": str(fm.get("summary") or ""), "first": first,
                      "text": title + "\n" + str(fm.get("summary") or "") + "\n" + page_text(body)}
    return pages, tax.get("domains", {})


def suggest(pages, domains, title, summary, exclude=(), top_pages=5):
    """(subject ranking, related-page ranking) for a topic given only its title and summary."""
    corpus = {r: p["text"] for r, p in pages.items() if r not in exclude}
    scorer = TfidfScorer(corpus)
    query = title + "\n" + summary
    page_scores, q = scorer.similarity(query)
    # a subject scores by the nearest pages that carry it (each votes with its similarity) and, a little, by its
    # description; voting over the nearest pages keeps a subject with one page from beating a well covered one
    nearest = sorted(page_scores.items(), key=lambda kv: -kv[1])[:NEIGHBOURS]
    subj = {}
    for key, info in domains.items():
        desc = scorer.cosine(q, scorer.query_vec((info.get("label") or "") + " " + (info.get("description") or "")))
        votes = [s for r, s in nearest if key in pages[r]["domains"]]
        subj[key] = {"score": sum(votes) / NEIGHBOURS + 0.3 * desc, "pages": len(votes)}
    best = sorted(page_scores.items(), key=lambda kv: -kv[1])[:top_pages]
    return (sorted(subj.items(), key=lambda kv: -kv[1]["score"]),
            [(r, s, scorer.shared_terms(q, r)) for r, s in best if s >= RELATED_MIN])


def evaluate(pages, domains):
    """Leave one page out, suggest from its title and summary (or first paragraph), compare with its own subjects."""
    labelled = {r: p for r, p in pages.items() if p["domains"]}
    hit1 = hit3 = total = 0
    rows = []
    for rel, p in sorted(labelled.items()):
        summary = p["summary"] or " ".join(p["first"].split()[:40])
        ranking, _ = suggest(pages, domains, p["title"], summary, exclude={rel})
        keys = [k for k, _ in ranking]
        h1 = keys[0] in p["domains"]
        h3 = any(k in p["domains"] for k in keys[:3])
        hit1, hit3, total = hit1 + h1, hit3 + h3, total + 1
        rows.append((rel, p["domains"], keys[:3], h1))
    return rows, hit1, hit3, total


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--title", help="title of the new topic")
    ap.add_argument("--summary", default="", help="one line about it (optional, improves the match)")
    ap.add_argument("--evaluate", action="store_true", help="leave-one-out check against the subjects pages already have")
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args()
    pages, domains = load(args.root)
    if args.evaluate:
        rows, h1, h3, n = evaluate(pages, domains)
        for rel, have, got, ok in rows:
            print("%s %-62s have %-34s suggested %s" % ("ok " if ok else "-- ", rel[:62], ",".join(have), ",".join(got)))
        print("\n%d pages with subjects: first suggestion is one of the page's subjects for %d (%d%%), one of the top 3 for %d (%d%%)"
              % (n, h1, round(100 * h1 / n), h3, round(100 * h3 / n)))
        return
    if not args.title:
        ap.error("give --title (or --evaluate)")
    ranking, near = suggest(pages, domains, args.title, args.summary)
    if not near:
        print("No existing page is close to this topic (nearest score under %.2f): it does not look related to anything here yet." % RELATED_MIN)
        print("Pick its subjects by hand; subjects suggested from unrelated pages would be guesses.")
        return
    print("Subjects (score; how many of the 5 nearest pages carry it). Read the top 3 as candidates, not a verdict:")
    for key, info in ranking[:4]:
        print("  %-24s %.2f  (%d pages)" % (key, info["score"], info["pages"]))
    print("\nClosest existing pages (score; shared words):")
    for rel, score, why in near:
        print("  %.2f  %-60s %s" % (score, rel, ", ".join(why)))


if __name__ == "__main__":
    main()
