#!/usr/bin/env python3
"""Fill the "Recently added" block of the root README.md from git history.

The block sits between <!-- recent:start --> and <!-- recent:end -->. The site
fills it at deploy time on its own (stage_site.py); this writes the same list
into the committed README so GitHub shows it too. Run it before opening a
dev -> main release PR and commit the result.

  python3 .docs/tools/update_recent.py          # rewrite README.md
  python3 .docs/tools/update_recent.py --check  # exit 1 if README.md is stale

Needs full git history. Standard library only.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import list_pages, submodule_paths  # noqa: E402
from stage_site import RECENT_RE, recent_pages, render_recent  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="change nothing; exit 1 if the block is stale")
    args = ap.parse_args()

    home = os.path.join(ROOT, "README.md")
    with open(home, encoding="utf-8", newline="") as f:
        text = f.read()
    if not RECENT_RE.search(text):
        sys.exit("README.md has no <!-- recent:start --> ... <!-- recent:end --> block")
    pages = list_pages(ROOT, set(submodule_paths(ROOT)))
    recent = recent_pages(ROOT, pages)
    if not recent:
        sys.exit("no git history found (a shallow clone cannot list added pages)")
    new = RECENT_RE.sub(lambda m: render_recent(ROOT, recent), text, count=1)
    if new == text:
        print("README.md is up to date")
        return 0
    if args.check:
        print("README.md 'Recently added' is stale; run python3 .docs/tools/update_recent.py and commit")
        return 1
    with open(home, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    print("README.md updated with %d pages" % len(recent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
