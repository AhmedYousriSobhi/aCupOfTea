#!/usr/bin/env python3
"""Write a small "share page" for every content page of the staged site.

Docsify pages live behind `#/` addresses, which link previews (chat apps, social
cards) cannot read: every shared link would show the home page card. A share page
is a tiny HTML file at the page's own folder address (`/fields/x/page/`) with that
page's title and summary as Open Graph tags, and an instant redirect to the real
page (`/#/fields/x/page`). No script is involved, so the site's CSP is unchanged.

  page.md              -> <out>/page/index.html     redirects to #/page
  folder/README.md     -> <out>/folder/index.html   redirects to #/folder/
  root README.md, code pages and generated pages get none.

Used by stage_site.py; the staged copy only, sources are never touched.
"""
import html
import os
import re
from urllib.parse import quote

import yaml

DEFAULT_BASE = "https://ahmedyousrisobhi.github.io/aCupOfTea/"
SITE_NAME = "aCupOfTea"
IMAGE = ".docs/icons/icon-512.png"
MAX_DESC = 200
SKIP_LINE = re.compile(r"^\s*(#|>|\||!\[|[-*+] |\d+\. |<|`{3}|:::|\$\$|---|===|\*{3}|\[!)")


def clean_inline(text):
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[*_`]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def shorten(text, limit=MAX_DESC):
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:.- ")
    return cut + "…"


def page_meta(text):
    """(title, description) of a page from its original text (front matter included)."""
    fm = {}
    body = text
    m = re.match(r"﻿?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.S)
    if m:
        try:
            loaded = yaml.safe_load(m.group(1))
            fm = loaded if isinstance(loaded, dict) else {}
        except yaml.YAMLError:
            fm = {}
        body = text[m.end():]
    title = str(fm.get("title") or "").strip()
    desc = str(fm.get("summary") or "").strip()
    paragraph, in_code = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not title and line.startswith("# "):
            title = line[2:].strip()
            continue
        if desc:
            continue
        if not line.strip():
            if paragraph:
                break
            continue
        if SKIP_LINE.match(line) and not paragraph:
            continue
        paragraph.append(line.strip())
    if not desc:
        desc = clean_inline(" ".join(paragraph))
    return clean_inline(title), shorten(clean_inline(desc))


def share_dir(page):
    """Folder (relative to the site root) that holds the share page, or None."""
    if page == "README.md":
        return None
    if page.endswith("/README.md"):
        return page[: -len("/README.md")]
    return page[: -len(".md")]


def route(page):
    d = share_dir(page)
    return "/" + d + ("/" if page.endswith("/README.md") else "")


def render(page, title, desc, base):
    d = share_dir(page)
    depth = d.count("/") + 1
    target = "../" * depth + "#" + quote(route(page), safe="/")
    url = base + quote(d, safe="/") + "/"
    t, ds = html.escape(title, quote=True), html.escape(desc, quote=True)
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        f"<title>{t}</title>",
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f'<meta http-equiv="refresh" content="0; url={html.escape(target, quote=True)}">',
        f'<link rel="canonical" href="{html.escape(url, quote=True)}">',
    ]
    if ds:
        lines.append(f'<meta name="description" content="{ds}">')
    lines += [
        '<meta property="og:type" content="article">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:title" content="{t}">',
    ]
    if ds:
        lines.append(f'<meta property="og:description" content="{ds}">')
    lines += [
        f'<meta property="og:url" content="{html.escape(url, quote=True)}">',
        f'<meta property="og:image" content="{base}{IMAGE}">',
        '<meta name="twitter:card" content="summary">',
        "</head>",
        "<body>",
        f'<p><a href="{html.escape(target, quote=True)}">{t}</a></p>',
        "</body>",
        "</html>",
        "",
    ]
    return "\n".join(lines)


def write_share_pages(out, sources, base=DEFAULT_BASE):
    """sources: {page path: original text}. Returns the number of share pages written."""
    if not base.endswith("/"):
        base += "/"
    written = 0
    # folder indexes first, so a page and a folder README with the same name keep the README
    for page in sorted(sources, key=lambda p: (not p.endswith("/README.md"), p)):
        d = share_dir(page)
        if d is None:
            continue
        target = os.path.join(out, d, "index.html")
        if os.path.exists(target):
            continue
        title, desc = page_meta(sources[page])
        if not title:
            title = os.path.basename(d)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as f:
            f.write(render(page, title, desc, base))
        written += 1
    return written
