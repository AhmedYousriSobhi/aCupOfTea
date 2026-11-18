#!/usr/bin/env python3
"""Backlinks: which pages link to a page ("Mentioned in"), for the staged site.

Built from the links the pages already contain, resolved the way check_links.py
resolves them (root-absolute links; `.md` optional; a folder address means its
README). A page counts once per target. Not counted: links from folder indexes
(a README with a `## Contents` list links to every page it lists, which says
nothing), from the page to itself, and from code and notebook pages.

Used by stage_site.py; nothing is written to the repository.
"""
import os
import re
from urllib.parse import unquote

from check_links import EXTERNAL_RE, links_in

CONTENTS = re.compile(r"^## +Contents\b", re.M)


def is_index(path, text):
    return os.path.basename(path) == "README.md" and (bool(CONTENTS.search(text)) or "/" not in path)


def resolve(target, pages):
    """The page a root-absolute link points at, or None."""
    if target.startswith("#") or EXTERNAL_RE.match(target) or not target.startswith("/"):
        return None
    rel = unquote(re.split(r"[?#]", target, 1)[0]).strip("/")
    if not rel:
        return "README.md" if "README.md" in pages else None
    for cand in (rel, rel + ".md", rel + "/README.md"):
        if cand in pages and cand.endswith(".md"):
            return cand
    return None


def build(texts):
    """{target page: [source pages]} from {page: text} (each list sorted, no duplicates)."""
    pages = set(texts)
    found = {}
    for src, text in texts.items():
        if is_index(src, text):
            continue
        for _, is_image, target in links_in(text):
            if is_image:
                continue
            dest = resolve(target, pages)
            if dest and dest != src:
                found.setdefault(dest, set()).add(src)
    return {k: sorted(v) for k, v in found.items()}


def render(sources, titles, summaries, limit=8):
    """The 'Mentioned in' block for the end of a page; '' without sources."""
    if not sources:
        return ""
    sources = sorted(sources, key=lambda p: (titles.get(p, p).lower(), p))
    lines = ['<!-- related-block -->', '<div class="mentioned-in">', "", "**Mentioned in**", ""]
    for p in sources[:limit]:
        line = f"- [{titles.get(p, p)}](/{p})"
        if summaries.get(p):
            line += f" — {summaries[p]}"
        lines.append(line)
    if len(sources) > limit:
        lines.append(f"- and {len(sources) - limit} more")
    return "\n".join(lines + ["", "</div>", ""])
