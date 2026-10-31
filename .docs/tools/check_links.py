#!/usr/bin/env python3
"""Check internal links in every page.

- A root-absolute link (/fields/x.md) must point at an existing file or folder.
- A ./ or ../ link breaks on the site (CLAUDE.md section 7) and is an error.
- An image (![](images/x.png)) is relative to the page and must exist.
- Git submodule paths, external links, #anchors, mailto: and code are skipped.
- Raw HTML that would run in readers' browsers is an error outside code:
  <script>, <iframe>, <object>, <embed>, on...= handlers in a tag, and
  javascript: links. A deliberate case is allowed by an
  `<!-- allow-html -->` comment on the line before it.
- Pictures without a real description (![](x), ![image](x), ![image.png](x)
  and similar) are listed as a warning, one line per page; they do not
  change the exit code. --no-alt-report silences the list.

Standard library only. Exits 1 on any problem.

Usage: python3 .docs/tools/check_links.py [--root PATH] [--no-alt-report]
"""
import argparse
import os
import re
import sys
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import list_pages, submodule_paths  # noqa: E402

LINK_RE = re.compile(r"(!?)\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
EXTERNAL_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.I)
UNSAFE_HTML = [
    (re.compile(r"<\s*(script|iframe|object|embed)\b", re.I), "raw <{0}> runs in readers' browsers"),
    (re.compile(r"<[a-z][^>]*\s(on[a-z]+)\s*=", re.I), "{0}= handler runs in readers' browsers"),
    (re.compile(r"(?:\]\(|href\s*=\s*[\"']?)\s*(javascript):", re.I), "{0}: link runs in readers' browsers"),
]
ALLOW = "<!-- allow-html -->"
IMAGE_ALT_RE = re.compile(r"!\[((?:[^\[\]]|\[[^\]]*\])*)\]\(")
NO_ALT_RE = re.compile(
    r"^(?:(?:image|img|picture|pic|photo|screenshot|figure|diagram|gif|video|alt)[\s_-]*\d*"
    r"|pasted image.*"
    r"|[\w .()-]*\.(?:png|jpe?g|gif|svg|webp|bmp|avif))?$",
    re.I)


def code_free_lines(text):
    """Yield (line number, line with inline code blanked) outside fenced code."""
    fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if FENCE_RE.match(line):
            fence = not fence
            continue
        if fence:
            continue
        yield n, INLINE_CODE_RE.sub(lambda c: " " * len(c.group(0)), line)


def links_in(text):
    """Yield (line, is_image, target) outside fenced and inline code."""
    for n, plain in code_free_lines(text):
        for m in LINK_RE.finditer(plain):
            yield n, bool(m.group(1)), m.group(2)


def missing_alt(text):
    """Yield the line of each picture whose description is empty or only a placeholder/file name."""
    for n, plain in code_free_lines(text):
        for m in IMAGE_ALT_RE.finditer(plain):
            if NO_ALT_RE.match(m.group(1).strip()):
                yield n


def unsafe_html(text):
    """Yield (line, message) for script-like raw HTML outside fenced and inline code."""
    fence, allowed = False, False
    for n, line in enumerate(text.splitlines(), 1):
        if FENCE_RE.match(line):
            fence = not fence
            continue
        if fence:
            continue
        if ALLOW in line:
            allowed = True
            continue
        plain = INLINE_CODE_RE.sub(lambda c: " " * len(c.group(0)), line)
        for rx, msg in UNSAFE_HTML:
            m = rx.search(plain)
            if m and not allowed:
                yield n, m.group(0).strip()[:40], msg.format(m.group(1).lower())
        allowed = False


def exists(root, rel):
    path = os.path.join(root, rel)
    return os.path.exists(path) or os.path.exists(path + ".md")


def check(root):
    subs = submodule_paths(root)
    problems = []
    for page in list_pages(root, subs):
        with open(os.path.join(root, page), encoding="utf-8") as fh:
            text = fh.read()
        for line, found, msg in unsafe_html(text):
            problems.append((page, line, found, msg + f"; remove it, or put {ALLOW} on the line before"))
        for line, is_image, target in links_in(text):
            if target.startswith("#") or EXTERNAL_RE.match(target):
                continue
            path = unquote(re.split(r"[?#]", target, 1)[0])
            if not path:
                continue
            if path.startswith("/"):
                rel = path.lstrip("/")
            elif is_image:
                rel = os.path.normpath(os.path.join(os.path.dirname(page), path)).replace(os.sep, "/")
            else:
                problems.append((page, line, target, "relative link breaks on the site; write it root-absolute"))
                continue
            if any(rel == s or rel.startswith(s + "/") for s in subs):
                continue
            if rel and not exists(root, rel):
                problems.append((page, line, target, "target does not exist"))
    return problems


def alt_report(root):
    """Return {page: [lines]} for pages with pictures that have no real description."""
    report = {}
    for page in list_pages(root, submodule_paths(root)):
        with open(os.path.join(root, page), encoding="utf-8") as fh:
            lines = list(missing_alt(fh.read()))
        if lines:
            report[page] = lines
    return report


def print_alt_report(report, gha):
    for page, lines in sorted(report.items()):
        shown = ", ".join(map(str, lines[:10])) + (", ..." if len(lines) > 10 else "")
        msg = f"{len(lines)} picture(s) without a description (lines {shown})"
        print(f"{page}: warning: {msg}")
        if gha:
            print(f"::warning file={page},line={lines[0]}::{msg}")
    total = sum(len(v) for v in report.values())
    print(f"{total} picture(s) on {len(report)} page(s) without a description (warning only)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    ap.add_argument("--no-alt-report", action="store_true",
                    help="do not list pictures without a description")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    problems = check(root)
    gha = os.environ.get("GITHUB_ACTIONS") == "true"
    if not args.no_alt_report:
        print_alt_report(alt_report(root), gha)
    for page, line, target, msg in sorted(problems):
        print(f"{page}:{line}: error: {target}: {msg}")
        if gha:
            print(f"::error file={page},line={line}::{target}: {msg}")
    print(f"{len(problems)} broken link(s) or unsafe HTML")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
