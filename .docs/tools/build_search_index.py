#!/usr/bin/env python3
"""Build the search index inside a staged site (stage_site.py calls this).

The site search (.docs/search.js) needs the text of every page. Without the
index it fetches all pages in the browser on first use (about 2 MB). The index
is two files, built from the staged pages, so it holds exactly the text the site
serves (front matter stripped; the related-pages strip is left out):

  .docs/index-titles.json  one entry per page: label, path, title, desc, type,
                           level, minutes, domains, tags. Small, loaded when the
                           search opens, and cached for offline use.
  .docs/index-body.json    path -> {secs: sections of text, code: fenced code}.
                           Loaded on the first search for text, not cached ahead.

A page's authored `summary` (front matter, read from .docs/generated/objects.json) is its description in the results; pages without one fall back to the first 120 characters of text. Folder labels lose their Markdown bold.

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
OUT_TITLES = ".docs/index-titles.json"
OUT_BODY = ".docs/index-body.json"
CODE_CAP = 30000  # characters of code kept per page


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


def load_meta(site):
    """path -> object from the staged .docs/generated/objects.json (summary, type, level, domains, tags)."""
    try:
        with open(os.path.join(site, ".docs/generated/objects.json"), encoding="utf-8") as f:
            objs = json.load(f)
    except (OSError, ValueError):
        return {}
    if isinstance(objs, dict):
        objs = objs.get("objects", list(objs.values()))
    return {o["path"]: o for o in objs if isinstance(o, dict) and o.get("path")}


def clean_label(label):
    """Sidebar labels of folders are bold (**Name**); the index holds plain text."""
    return re.sub(r"\s+", " ", label.replace("**", "")).strip()


def code_of(text):
    """The fenced code of a page, one block after another, capped."""
    blocks = re.findall(r"```[^\n]*\n([\s\S]*?)```", text)
    return "\n".join(b.strip("\n") for b in blocks)[:CODE_CAP]


def index_page(page, text, summary="", meta=None):
    text = re.sub(r"^﻿?---[ \t]*\r?\n[\s\S]*?\r?\n---[ \t]*(\r?\n|$)", "", text, count=1)
    text = re.sub(r"<!-- related-block -->[\s\S]*?</div>", " ", text)  # links to other pages are not page text
    code = code_of(text)
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
    label = clean_label(page["label"])
    desc = re.sub(r"\s+", " ", re.sub(r"[`*_]", "", summary)).strip() if summary else (utf16_prefix(first["body"], 120) if first else "")
    meta = meta or {}
    entry = {
        "label": label,
        "path": page["path"],
        "title": plain(h1 or label),
        "desc": desc,
        "secs": out,
        "code": code,
    }
    for key, src in (("type", "type"), ("level", "level"), ("min", "reading_time_min"),
                     ("domains", "domains"), ("tags", "tags")):
        if meta.get(src):
            entry[key] = meta[src]
    return entry


def build(site):
    titles, bodies = [], {}
    metas = load_meta(site)
    for page in sidebar_pages(site):
        key = unquote(page["path"])
        full = os.path.join(site, key)
        text = ""
        if os.path.isfile(full):
            with open(full, encoding="utf-8", newline="") as f:
                text = f.read()
        meta = metas.get(key, {})
        entry = index_page(page, text, meta.get("summary", ""), meta)
        body = {"secs": entry.pop("secs")}
        code = entry.pop("code")
        if code:
            body["code"] = code
        titles.append(entry)
        bodies[page["path"]] = body
    sizes = []
    for name, data in ((OUT_TITLES, titles), (OUT_BODY, bodies)):
        dest = os.path.join(site, name)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        sizes.append(os.path.getsize(dest))
    return len(titles), sizes[0], sizes[1]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pages, t, b = build(sys.argv[1])
    print(f"search index: {pages} pages, titles {t / 1024:.0f} KB, bodies {b / 1024:.0f} KB")


if __name__ == "__main__":
    main()
