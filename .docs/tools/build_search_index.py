#!/usr/bin/env python3
"""Build .docs/search-index.json inside a staged site (stage_site.py calls this).

The site search (.docs/search.js) needs the text of every page. Without this
file it fetches all ~155 pages in the browser on first use (about 2 MB). With
it, one request is enough. The index is built from the staged pages, so it holds
exactly the text the site serves (front matter stripped, Related block added).

The parsing here mirrors the crawl in search.js on purpose: the same pages, the
same sections, the same plain-text rules. Change one and change the other.

Usage: python3 .docs/tools/build_search_index.py SITE_DIR
"""
import json
import os
import re
import sys
import unicodedata
from urllib.parse import unquote

SIDEBAR = ".docs/_sidebar.md"
OUT = ".docs/search-index.json"


def slug(heading):
    s = re.sub(r"<[^>]+>", "", heading).lower().replace("'", "39").strip()
    s = "".join(c for c in s
                if c.isspace() or c in "_-" or unicodedata.category(c)[0] in "LN")
    s = re.sub(r"\s+", "-", s)
    return "_" + s if re.match(r"\d", s) else s


def plain(s):
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[`*_>|#]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def utf16_prefix(s, units):
    """First `units` UTF-16 code units of s, as JavaScript's slice(0, units) would."""
    return s.encode("utf-16-le")[: units * 2].decode("utf-16-le", errors="ignore")


def sidebar_pages(site):
    with open(os.path.join(site, SIDEBAR), encoding="utf-8") as f:
        side = f.read()
    pages, seen = [], set()
    for label, path in re.findall(r"\[([^\]]+)\]\(([^)\s]+\.md)\)", side):
        path = path.lstrip("/")
        if not re.match(r"https?:", path) and path not in seen:
            seen.add(path)
            pages.append({"label": label, "path": path})
    if "README.md" not in seen:
        pages.insert(0, {"label": "Home", "path": "README.md"})
    return pages


def index_page(page, text):
    text = re.sub(r"^﻿?---[ \t]*\r?\n[\s\S]*?\r?\n---[ \t]*(\r?\n|$)", "", text, count=1)
    text = re.sub(r"```[\s\S]*?```", " ", text)
    secs, cur, h1 = [], {"head": "", "id": "", "text": []}, ""
    for line in re.split(r"\r?\n", text):
        m = re.match(r"^(#{1,3}) +(.+?)\s*#*\s*$", line)
        if m:
            secs.append(cur)
            if m.group(1) == "#" and not h1:
                h1 = m.group(2)
            cur = {"head": m.group(2), "id": slug(m.group(2)), "text": []}
        else:
            cur["text"].append(line)
    secs.append(cur)

    out = []
    for s in secs:
        head, body = plain(s["head"]), plain(" ".join(s["text"]))
        if (head or body) and not re.match(r"^table of contents?$", head, re.I):
            out.append({"head": head, "id": s["id"], "body": body})
    first = next((s for s in out if len(s["body"]) > 40), None)
    return {
        "label": page["label"],
        "path": page["path"],
        "title": plain(h1 or page["label"]),
        "desc": utf16_prefix(first["body"], 120) if first else "",
        "secs": out,
    }


def build(site):
    index = []
    for page in sidebar_pages(site):
        full = os.path.join(site, unquote(page["path"]))
        text = ""
        if os.path.isfile(full):
            with open(full, encoding="utf-8", newline="") as f:
                text = f.read()
        index.append(index_page(page, text))
    dest = os.path.join(site, OUT)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    return len(index), os.path.getsize(dest)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pages, size = build(sys.argv[1])
    print(f"search index: {pages} pages, {size / 1024:.0f} KB -> {OUT}")


if __name__ == "__main__":
    main()
