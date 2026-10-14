#!/usr/bin/env python3
"""Check internal links in every page.

- A root-absolute link (/fields/x.md) must point at an existing file or folder.
- A ./ or ../ link breaks on the site (CLAUDE.md section 7) and is an error.
- An image (![](images/x.png)) is relative to the page and must exist.
- Git submodule paths, external links, #anchors, mailto: and code are skipped.

Standard library only. Exits 1 on any problem.

Usage: python3 .docs/tools/check_links.py [--root PATH]
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


def links_in(text):
    """Yield (line, is_image, target) outside fenced and inline code."""
    fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if FENCE_RE.match(line):
            fence = not fence
            continue
        if fence:
            continue
        for m in LINK_RE.finditer(INLINE_CODE_RE.sub(lambda c: " " * len(c.group(0)), line)):
            yield n, bool(m.group(1)), m.group(2)


def exists(root, rel):
    path = os.path.join(root, rel)
    return os.path.exists(path) or os.path.exists(path + ".md")


def check(root):
    subs = submodule_paths(root)
    problems = []
    for page in list_pages(root, subs):
        with open(os.path.join(root, page), encoding="utf-8") as fh:
            text = fh.read()
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


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    root = os.path.abspath(ap.parse_args().root)
    problems = check(root)
    gha = os.environ.get("GITHUB_ACTIONS") == "true"
    for page, line, target, msg in sorted(problems):
        print(f"{page}:{line}: error: {target}: {msg}")
        if gha:
            print(f"::error file={page},line={line}::{target}: {msg}")
    print(f"{len(problems)} broken link(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
