#!/usr/bin/env python3
"""Prototype: suggest subjects and related pages for a new topic from its text (issue #198).

Scores a title and summary against each subject's description and against the existing pages
(TF-IDF cosine, pure Python, no new dependency) and prints the subjects and closest pages with
a score and the reason. The scoring sits behind `suggest()` so another backend (embeddings) can
replace it later. The hand-written `related` lists in taxonomy.yaml stay an override; this
only suggests.

Usage:
  python3 .docs/tools/suggest_subjects.py "Title" ["one-line summary"]
  python3 .docs/tools/suggest_subjects.py --pair SUBJECT SUBJECT   # evidence for a pair
  python3 .docs/tools/suggest_subjects.py --evaluate     # leave-one-out check on the repo's own pages
"""
import argparse
import json
import math
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

STOP = frozenset("""a an and are as at be by for from how in into is it its of on or that the this to
what when where which why with without your you we vs via about not can do does using use""".split())


def tokens(text):
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP or len(w) < 2:
            continue
        # a crude plural/-ing stem is enough for short titles
        for suf in ("ing", "es", "s"):
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                w = w[: -len(suf)]
                break
        out.append(w)
    return out


class Index:
    """TF-IDF over short documents: one per page, one per subject (description + its pages)."""

    def __init__(self, docs):
        self.tf = {k: Counter(tokens(v)) for k, v in docs.items()}
        df = Counter(t for c in self.tf.values() for t in c)
        n = len(docs)
        self.idf = {t: math.log((1 + n) / (1 + d)) + 1 for t, d in df.items()}
        self.vec = {k: self._norm(c) for k, c in self.tf.items()}

    def _norm(self, counts):
        v = {t: (1 + math.log(c)) * self.idf.get(t, 1.0) for t, c in counts.items()}
        size = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / size for t, x in v.items()}

    def query(self, text):
        return self._norm(Counter(tokens(text)))

    @staticmethod
    def cosine(a, b):
        if len(a) > len(b):
            a, b = b, a
        return sum(x * b.get(t, 0.0) for t, x in a.items())

    def shared(self, a, key, n=4):
        """The words that contribute most to the match between query vector `a` and document `key`."""
        b = self.vec[key]
        ranked = sorted(((x * b[t], t) for t, x in a.items() if t in b), reverse=True)
        return [t for _, t in ranked[:n]]


def page_text(p):
    return " ".join([p["title"]] * 2 + [p.get("summary") or ""] + list(p.get("tags") or []))


def load(root=ROOT):
    with open(os.path.join(root, ".docs/generated/objects.json"), encoding="utf-8") as f:
        objects = json.load(f)
    import yaml
    with open(os.path.join(root, ".docs/metadata/taxonomy.yaml"), encoding="utf-8") as f:
        taxonomy = yaml.safe_load(f)
    return objects, taxonomy


def suggest(title, summary, objects, taxonomy, skip_id=None, top_pages=5, top_subjects=3, skip_path=None):
    """Return {"subjects": [(key, score, reason)], "pages": [(id, score, reason)]}.

    subject score = 0.4 * match with the subject's description + 0.6 * the best-matching pages that carry it.
    """
    pages = {k: v for k, v in objects.items() if k != skip_id and v.get("title") and (skip_path is None or v.get("path") != skip_path)}
    domains = taxonomy.get("domains", {})
    docs = {"page:" + k: page_text(v) for k, v in pages.items()}
    for d, meta in domains.items():
        docs["subject:" + d] = " ".join([meta.get("label", ""), meta.get("description", "")] * 2)
    index = Index(docs)
    q = index.query(" ".join([title] * 2 + [summary or ""]))

    sims = {k: index.cosine(q, index.vec["page:" + k]) for k in pages}
    ranked = sorted(sims.items(), key=lambda kv: (-kv[1], kv[0]))
    nearest = [(k, s) for k, s in ranked if s > 0][:top_pages]

    scores = {}
    for d in domains:
        desc = index.cosine(q, index.vec["subject:" + d])
        carried = sorted((s for k, s in sims.items() if d in (pages[k].get("domains") or [])), reverse=True)[:3]
        votes = sum(carried) / 3.0
        scores[d] = (0.4 * desc + 0.6 * votes, desc, votes)

    subjects = []
    for d, (score, desc, votes) in sorted(scores.items(), key=lambda kv: (-kv[1][0], kv[0]))[:top_subjects]:
        if score <= 0:
            continue
        via = [pages[k]["title"] for k, _ in nearest if d in (pages[k].get("domains") or [])][:2]
        words = index.shared(q, "subject:" + d)
        why = []
        if words:
            why.append("words in its description: " + ", ".join(words))
        if via:
            why.append("similar pages carry it: " + "; ".join(via))
        subjects.append((d, score, " | ".join(why) or "weak match"))

    related = []
    for k, s in nearest:
        words = index.shared(q, "page:" + k)
        related.append((k, s, "shares: " + ", ".join(words)))
    return {"subjects": subjects, "pages": related}


def pair_evidence(a, b, objects, taxonomy, top_words=5):
    """Why two subjects do or do not go together: {"declared", "pages", "words", "score"}.

    declared = the hand-written `related` list says so (it stays the override); pages = titles of pages
    that carry both; words = the vocabulary the two subjects share (their descriptions plus their pages);
    score = TF-IDF cosine between the two subjects' texts.
    """
    domains = taxonomy.get("domains", {})
    declared = b in (domains.get(a, {}).get("related") or []) or a in (domains.get(b, {}).get("related") or [])
    carry = lambda d: [v for v in objects.values() if v.get("title") and d in (v.get("domains") or [])]
    both = sorted(v["title"] for v in carry(a) if b in (v.get("domains") or []))
    docs = {}
    for d in (a, b):
        meta = domains.get(d, {})
        docs[d] = " ".join([meta.get("label", ""), meta.get("description", "")] * 2 + [page_text(v) for v in carry(d)])
    index = Index({"x:" + a: docs[a], "x:" + b: docs[b]})
    va, vb = index.vec["x:" + a], index.vec["x:" + b]
    words = [t for _, t in sorted(((va[t] * vb[t], t) for t in va if t in vb), reverse=True)[:top_words]]
    return {"declared": declared, "pages": both, "words": words, "score": index.cosine(va, vb)}


def explain_pair(a, b, objects, taxonomy):
    """One line of evidence for a pair of subjects, for a warning or a prompt."""
    e = pair_evidence(a, b, objects, taxonomy)
    bits = ["listed as related in taxonomy.yaml" if e["declared"] else "not listed as related in taxonomy.yaml"]
    n = len(e["pages"])
    bits.append(("1 page carries both" if n == 1 else "%d pages carry both" % n) if n else "no page carries both")
    if e["words"]:
        bits.append("shared words: " + ", ".join(e["words"]) + " (similarity %.2f)" % e["score"])
    else:
        bits.append("no shared vocabulary")
    return "; ".join(bits)


def pairs_for_root(root, subjects):
    """[(a, b, evidence line)] for every pair of `subjects`; empty when the generated index is missing."""
    try:
        objects, taxonomy = load(root)
    except (OSError, ValueError):
        return []
    return [(a, b, explain_pair(a, b, objects, taxonomy)) for i, a in enumerate(subjects) for b in subjects[i + 1:]]


def for_root(root, title, summary="", skip_path=None):
    """suggest() for the repo at `root`; empty when the title is blank or the generated index is missing."""
    empty = {"subjects": [], "pages": []}
    if not (title or "").strip():
        return empty
    try:
        objects, taxonomy = load(root)
    except (OSError, ValueError):
        return empty
    return suggest(title, summary, objects, taxonomy, skip_path=skip_path)


def evaluate(objects, taxonomy, limit=None):
    """Leave one page out, suggest from its title and summary, compare with the domains it really has."""
    hit1 = hit_any = total = 0
    for k, p in sorted(objects.items())[:limit]:
        real = set(p.get("domains") or [])
        if not real or not p.get("summary"):
            continue
        got = suggest(p["title"], p["summary"], objects, taxonomy, skip_id=k)["subjects"]
        names = [d for d, _, _ in got]
        total += 1
        hit1 += bool(names and names[0] in real)
        hit_any += bool(real & set(names))
    return total, hit1, hit_any


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("title", nargs="?")
    ap.add_argument("summary", nargs="?", default="")
    ap.add_argument("--evaluate", action="store_true", help="leave-one-out check on the repo's own pages")
    ap.add_argument("--pair", nargs=2, metavar=("A", "B"), help="evidence for two subjects going together")
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args(argv)
    objects, taxonomy = load(args.root)
    if args.evaluate:
        total, hit1, hit_any = evaluate(objects, taxonomy)
        print("pages checked: %d" % total)
        print("top suggestion is one of the page's real subjects: %d (%.0f%%)" % (hit1, 100.0 * hit1 / max(total, 1)))
        print("one of the top 3 is a real subject:               %d (%.0f%%)" % (hit_any, 100.0 * hit_any / max(total, 1)))
        return 0
    if args.pair:
        a, b = args.pair
        for k in (a, b):
            if k not in taxonomy.get("domains", {}):
                ap.error("unknown subject: " + k)
        print("%s + %s: %s" % (a, b, explain_pair(a, b, objects, taxonomy)))
        for t in pair_evidence(a, b, objects, taxonomy)["pages"]:
            print("  carries both: " + t)
        return 0
    if not args.title:
        ap.error("give a title, or --evaluate")
    out = suggest(args.title, args.summary, objects, taxonomy)
    print("Subjects:")
    for d, s, why in out["subjects"] or [("(none)", 0, "no word in common with any subject or page")]:
        print("  %-28s %.2f  %s" % (d, s, why))
    print("Closest pages:")
    for k, s, why in out["pages"]:
        print("  %-40s %.2f  %s" % (k, s, why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
