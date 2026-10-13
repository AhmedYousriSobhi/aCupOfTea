#!/usr/bin/env python3
"""Build the publishable copy of the site (the "staging copy").

Copies the repo to --out, then in the COPY only:
  * strips YAML front matter from every page (LF or CRLF), so Docsify
    rendering and its search index stay clean;
  * appends a "Related" block to pages that have relations, from
    .docs/generated/related.json (run generate_index.py first).
Source files are never modified. Local `docsify serve` on the repo itself
shows neither the stripping nor the Related block; serve --out to see them.

Usage: python3 .docs/tools/stage_site.py --out _site [--src PATH]
"""
import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import list_pages, split_front_matter, submodule_paths  # noqa: E402

MARKER = ".stage-site"
RELATED_MARK = "<!-- related-block -->"


def render_related(block):
    parts = [RELATED_MARK, "", "---", "", "## Related", ""]
    for key, label in (("prerequisites", "Prerequisites"),
                       ("required_by", "Required by"),
                       ("related", "See also")):
        items = block.get(key) or []
        if not items:
            continue
        parts += [f"**{label}**", ""]
        parts += [f"- [{i['title']}](/{i['path']})" for i in items]
        parts.append("")
    return "\n".join(parts)


def stage(src, out):
    src, out = os.path.abspath(src), os.path.abspath(out)
    if out == src or src.startswith(out + os.sep):
        sys.exit("--out must not be the source directory or one of its parents")
    if os.path.exists(out):
        if not os.path.exists(os.path.join(out, MARKER)):
            sys.exit(f"{out} exists and was not created by this script; refusing to delete it")
        shutil.rmtree(out)

    subs = set(submodule_paths(src))
    out_rel = os.path.relpath(out, src).replace(os.sep, "/")

    def ignore(dirpath, names):
        rel_dir = os.path.relpath(dirpath, src).replace(os.sep, "/")
        skip = set()
        for n in names:
            rel = n if rel_dir == "." else f"{rel_dir}/{n}"
            if n == ".git" or rel in subs or rel == out_rel:
                skip.add(n)
        return skip

    shutil.copytree(src, out, ignore=ignore)
    for s in sorted(subs):  # keep submodule folders as empty dirs, as in a CI checkout
        os.makedirs(os.path.join(out, s), exist_ok=True)

    related = {}
    rpath = os.path.join(src, ".docs/generated/related.json")
    if os.path.exists(rpath):
        with open(rpath, encoding="utf-8") as f:
            related = json.load(f)

    stripped = appended = 0
    for path in list_pages(out, set(subs)):
        full = os.path.join(out, path)
        with open(full, encoding="utf-8", newline="") as f:
            text = f.read()
        new = text
        split = split_front_matter(text)
        if split is not None:
            new = text[split[1]:]
            stripped += 1
        if path in related:
            new = new.rstrip("\r\n") + "\n\n" + render_related(related[path]) + "\n"
            appended += 1
        if new != text:
            with open(full, "w", encoding="utf-8", newline="") as f:
                f.write(new)

    open(os.path.join(out, ".nojekyll"), "w").close()
    open(os.path.join(out, MARKER), "w").close()
    print(f"staged {out}: stripped front matter from {stripped} pages, "
          f"appended Related to {appended} pages")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    stage(args.src, args.out)


if __name__ == "__main__":
    main()
