#!/usr/bin/env python3
"""A small Markdown to static HTML renderer for the share pages (issue #274).

The share page of a content page carries the page's text, so search engines and
readers without JavaScript get it; Docsify takes over for browsers that run
scripts (a script file redirects them to the `#/` page). Only what the pages use
is handled: headings, paragraphs, lists, block quotes, fenced code, tables,
images, links, bold, italic and inline code. Raw HTML, math and Docsify
extensions are left out; everything else is escaped, so no source text can add
markup or script.

Used by share_pages.py; the staged copy only, sources are never touched.
"""
import html
import posixpath
import re
from urllib.parse import quote

FRONT = re.compile(r"﻿?---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|$)", re.S)
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
BULLET = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
INLINE = re.compile(
    r"(?P<code>`+)(?P<c>.+?)(?P=code)"
    r"|!\[(?P<alt>[^\]]*)\]\((?P<isrc>[^)\s]+)(?:\s+\"[^\"]*\")?\)"
    r"|\[(?P<text>[^\]]*)\]\((?P<href>[^)\s]+)(?:\s+\"[^\"]*\")?\)"
    r"|\*\*(?P<b>[^*]+?)\*\*|__(?P<b2>[^_]+?)__"
    r"|(?<![*\w])\*(?P<i>[^*\s][^*]*?)\*(?!\w)|(?<![_\w])_(?P<i2>[^_\s][^_]*?)_(?!\w)")


def esc(s):
    return html.escape(s, quote=True)


def strip_front_matter(text):
    m = FRONT.match(text)
    return text[m.end():] if m else text


def make_url(url, page, depth):
    """Point a link of a source page at the staged copy, relative to the share page.

    page: source path of the page (a/b.md); depth: folders between the share page and the site root.
    """
    url = url.strip().strip("<>")
    if re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I):
        return url if re.match(r"^(https?|mailto):", url, re.I) else ""
    if url.startswith("#"):
        return ""  # a section of the interactive page; nothing to jump to here
    path, _, frag = url.partition("#")
    if not path:
        return ""
    if path.startswith("/"):
        target = path.lstrip("/")
    else:
        target = posixpath.normpath(posixpath.join(posixpath.dirname(page), path))
    if target.startswith(".."):
        return ""
    rel = "../" * depth + target
    if target.endswith(".md"):
        rel = rel[:-3]
        rel = rel[:-len("README")] if rel.endswith("/README") else rel
        rel = rel + "/" if rel and not rel.endswith("/") else rel or "./"
        if target == "README.md":
            rel = "../" * depth or "./"
    return quote(rel, safe="/.:-_~") + (("#" + quote(frag, safe="-_.~")) if frag and not target.endswith(".md") else "")


def inline(text, page, depth):
    out, pos = [], 0
    for m in INLINE.finditer(text):
        out.append(esc(text[pos:m.start()]))
        pos = m.end()
        if m.group("c") is not None:
            out.append(f"<code>{esc(m.group('c').strip())}</code>")
        elif m.group("isrc") is not None:
            src = make_url(m.group("isrc"), page, depth)
            alt = esc(m.group("alt"))
            out.append(f'<img src="{esc(src)}" alt="{alt}" loading="lazy">' if src else alt)
        elif m.group("href") is not None:
            href = make_url(m.group("href"), page, depth)
            label = inline(m.group("text"), page, depth)
            out.append(f'<a href="{esc(href)}">{label}</a>' if href else label)
        elif m.group("b") is not None or m.group("b2") is not None:
            out.append(f"<strong>{esc(m.group('b') or m.group('b2'))}</strong>")
        else:
            out.append(f"<em>{esc(m.group('i') or m.group('i2'))}</em>")
    out.append(esc(text[pos:]))
    return "".join(out)


def cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


def render_list(lines, i, page, depth):
    """Render the list starting at lines[i]; returns (html, next index). Nested lists by indent."""
    indent = len(BULLET.match(lines[i]).group(1))
    ordered = BULLET.match(lines[i]).group(2)[0].isdigit()
    tag = "ol" if ordered else "ul"
    items = []
    while i < len(lines):
        m = BULLET.match(lines[i])
        if not m or len(m.group(1)) < indent:
            break
        if len(m.group(1)) > indent:
            sub, i = render_list(lines, i, page, depth)
            if items:
                items[-1] += sub
            continue
        item = inline(m.group(3), page, depth)
        i += 1
        while i < len(lines) and lines[i].strip() and not BULLET.match(lines[i]) and lines[i].startswith(" "):
            item += " " + inline(lines[i].strip(), page, depth)
            i += 1
        items.append(item)
    return f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>", i


def render_body(text, page, depth):
    """HTML of a page's Markdown (front matter and the first H1 are the caller's business)."""
    lines = strip_front_matter(text).splitlines()
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(s.strip() for s in para), page, depth) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        fence = re.match(r"^\s*(`{3,}|~{3,})\s*([\w+-]*)", line)
        if fence:
            flush()
            i += 1
            code = []
            while i < len(lines) and not lines[i].lstrip().startswith(fence.group(1)):
                code.append(lines[i])
                i += 1
            i += 1
            lang = re.sub(r"[^\w+-]", "", fence.group(2))
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{esc(chr(10).join(code))}</code></pre>")
            continue
        h = HEADING.match(line)
        if h:
            flush()
            n = len(h.group(1))
            out.append(f"<h{n}>{inline(h.group(2), page, depth)}</h{n}>")
        elif not line.strip():
            flush()
        elif line.lstrip().startswith("<"):
            flush()  # raw HTML is left out
        elif line.lstrip().startswith(">"):
            flush()
            quote_lines = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote_lines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + render_body("\n".join(quote_lines), page, depth) + "</blockquote>")
            continue
        elif BULLET.match(line):
            flush()
            block, i = render_list(lines, i, page, depth)
            out.append(block)
            continue
        elif "|" in line and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]) and "-" in lines[i + 1]:
            flush()
            head = cells(line)
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(cells(lines[i]))
                i += 1
            t = "<table><thead><tr>" + "".join(f"<th>{inline(c, page, depth)}</th>" for c in head) + "</tr></thead><tbody>"
            for r in rows:
                t += "<tr>" + "".join(f"<td>{inline(c, page, depth)}</td>" for c in r) + "</tr>"
            out.append(t + "</tbody></table>")
            continue
        elif re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
            flush()
            out.append("<hr>")
        elif re.match(r"^\s*\$\$", line):
            flush()  # display math needs KaTeX; the interactive page has it
            if not re.match(r"^\s*\$\$.*\$\$\s*$", line):
                i += 1
                while i < len(lines) and "$$" not in lines[i]:
                    i += 1
        else:
            para.append(line)
        i += 1
    flush()
    return "\n".join(out)
