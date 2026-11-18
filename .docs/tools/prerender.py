#!/usr/bin/env python3
"""Render a page's Markdown to plain static HTML for its share page.

A share page (share_pages.py) sits at a page's own folder address. With this
module it carries the page itself: title, headings, text, lists, tables, code
and links, readable by a reader without JavaScript and by any crawler. Readers
with JavaScript never see it: `.docs/share-redirect.js` sends them on to the
`#/` page before the body is painted, where Docsify draws the page as usual. So
the static copy only needs to be readable, not identical to what Docsify draws
(formulas stay LaTeX, diagrams stay code, tabs are shown one after the other).

Links are rewritten for the share page's own address (one or more folders
deep): a link to another page goes to that page's share page, a code file or
other page with no share page to its `#/` address, a picture or data file to
the file itself. The renderer is markdown-it-py (pure Python, CommonMark plus
tables and strikethrough, the GitHub-flavoured parts Docsify's marked also
draws). Without it, `available()` is False and the share page stays a plain
redirect with the summary.

Used by share_pages.py on the staged copy only; sources are never touched.
"""
import html
import posixpath
import re
from urllib.parse import quote, unquote

try:
    from markdown_it import MarkdownIt
except ImportError:  # optional: the share page falls back to a redirect only
    MarkdownIt = None

from code_pages import BRANCH, REPO
from pagemodel import Page

SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:|^//")
HTML_ATTR = re.compile(r'''(\s(?:src|href)=)(["'])([^"']*)\2''', re.I)
# Docsify's heading slugs: lower case, punctuation dropped, spaces to hyphens
SLUG_DROP = re.compile(r"[ -⁯⸀-⹿\\'!\"#$%&()*+,./:;<=>?@\[\]^`{|}~]")

_md = None


def available():
    return MarkdownIt is not None


def renderer():
    global _md
    if _md is None:
        _md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
    return _md


def slug(text, seen):
    s = SLUG_DROP.sub("", re.sub(r"<[^>]*>", "", text.strip().lower()))
    s = re.sub(r"\s", "-", s)
    n = seen.get(s, 0)
    seen[s] = n + 1
    return s if n == 0 else f"{s}-{n}"


def share_address(page):
    """Folder (from the site root) of a page's share page; None for the home page."""
    if page == "README.md":
        return None
    if page.endswith("/README.md"):
        return page[: -len("README.md")]
    return page[: -len(".md")] + "/"


class Links:
    """Rewrites the links of one page for its share page."""

    def __init__(self, page, up, pages, exists=None):
        self.dir = posixpath.dirname(page)
        self.up = up              # "../../": from the share page back to the site root
        self.pages = pages        # every page that has a share page (or is the home page)
        self.exists = exists      # is this path (from the site root) a file of the site? None: assume so

    def resolve(self, url):
        """(path from the site root, query, fragment) of a local link, or None for an external one."""
        if not url or SCHEME.match(url) or url.startswith("#/"):
            return None
        path, _, frag = url.partition("#")
        path, _, query = path.partition("?")
        path = unquote(path)
        if path.startswith("/"):
            full = path.lstrip("/")
        else:
            full = posixpath.join(self.dir, path) if path else ""
        full = posixpath.normpath(full) if full else ""
        if full in (".", ""):
            full = ""
        if full.startswith(".."):
            return None
        return full, query, frag

    def href(self, url):
        if url.startswith("#/"):
            return self.up + url
        if url.startswith("#") or SCHEME.match(url or ""):
            return url
        r = self.resolve(url)
        if r is None:
            return url
        full, query, frag = r
        m = re.search(r"(?:^|&)id=([^&]+)", query)
        section = m.group(1) if m else frag
        anchor = ("#" + section) if section else ""
        if full == "":
            return self.up  # the home page (a section there would read as a Docsify route)
        page = full if full.endswith(".md") else None
        if page is None and (full + "/README.md") in self.pages:
            page = full + "/README.md"
        if page is None and (full + ".md") in self.pages:
            page = full + ".md"
        if page in self.pages:
            addr = share_address(page)
            if addr is None:
                return self.up
            return self.up + quote(addr, safe="/") + anchor
        if page is not None or full.endswith((".py", ".ipynb", ".sh")):
            # a page without a share page, or a code file Docsify shows as a page
            route = "/" + full[:-3] if full.endswith(".md") else "/" + full
            return self.up + "#" + quote(route, safe="/") + (f"?id={section}" if section else "")
        if self.exists is not None and not self.exists(full):
            # a folder with no page (data, a git submodule): its view on GitHub, as from the repository
            return f"https://github.com/{REPO}/tree/{BRANCH}/" + quote(full, safe="/")
        return self.up + quote(full, safe="/") + ("#" + frag if frag else "")

    def src(self, url):
        r = self.resolve(url)
        if r is None:
            return url
        return self.up + quote(r[0], safe="/")

    def raw_html(self, text):
        def fix(m):
            attr, q, url = m.group(1), m.group(2), m.group(3)
            new = self.src(url) if attr.strip().lower().startswith("src") else self.href(url)
            return f"{attr}{q}{html.escape(new, quote=True)}{q}"
        return HTML_ATTR.sub(fix, text)


def body_html(page, text, up, pages, exists=None):
    """The page body (front matter dropped) as HTML, links rewritten; '' without the renderer.

    `exists(path)` tells whether a path from the site root is a file of the site; a link to
    anything else (a folder with no page, a submodule) goes to its view on GitHub."""
    if not available():
        return ""
    body = Page.from_text(page, text).body
    md = renderer()
    tokens = md.parse(body)
    links = Links(page, up, pages, exists)
    seen = {}
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and i + 1 < len(tokens):
            tok.attrSet("id", slug(tokens[i + 1].content, seen))
        elif tok.type == "html_block":
            tok.content = links.raw_html(tok.content)
        for child in tok.children or ():
            if child.type == "link_open":
                child.attrSet("href", links.href(child.attrGet("href") or ""))
            elif child.type == "image":
                child.attrSet("src", links.src(child.attrGet("src") or ""))
                child.attrSet("loading", "lazy")
                child.attrs.pop("title", None)  # Docsify size hints (':size=..') are not titles
            elif child.type == "html_inline":
                child.content = links.raw_html(child.content)
    return md.renderer.render(tokens, md.options, {})
