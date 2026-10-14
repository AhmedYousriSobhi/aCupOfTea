#!/usr/bin/env python3
"""Build the publishable copy of the site (the "staging copy").

Copies the repo to --out, then in the COPY only:
  * strips YAML front matter from every page (LF or CRLF), so Docsify
    rendering and its search index stay clean;
  * appends a "Related" block to pages that have relations, from
    .docs/generated/related.json (run generate_index.py first);
  * writes .docs/last-updated.json (page -> date of its last git commit) for
    the page footer, when the checkout has git history;
  * writes .docs/search-index.json (build_search_index.py) so the site search
    loads one file instead of fetching every page.
Source files are never modified. Local `docsify serve` on the repo itself
shows neither the stripping nor the Related block; serve --out to see them.

Usage: python3 .docs/tools/stage_site.py --out _site [--src PATH]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_search_index import build as build_search_index  # noqa: E402
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


def last_updated(src, pages):
    """{page: 'YYYY-MM-DD'} from one git log pass; {} when there is no usable history."""
    try:
        log = subprocess.run(["git", "-C", src, "log", "--format=@%cs", "--name-only", "-M"],
                             capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    wanted, dates, day = set(pages), {}, None
    for line in log.splitlines():
        if line.startswith("@"):
            day = line[1:]
        elif line in wanted and line not in dates:
            dates[line] = day  # newest commit comes first
    return dates


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

    dates = last_updated(src, list_pages(out, set(subs)))
    if dates:
        with open(os.path.join(out, ".docs/last-updated.json"), "w", encoding="utf-8") as f:
            json.dump(dates, f, sort_keys=True, separators=(",", ":"))

    n_idx, idx_size = build_search_index(out)

    open(os.path.join(out, ".nojekyll"), "w").close()
    open(os.path.join(out, MARKER), "w").close()
    print(f"staged {out}: stripped front matter from {stripped} pages, "
          f"appended Related to {appended} pages, "
          f"last-updated dates for {len(dates)} pages, "
          f"search index of {n_idx} pages ({idx_size // 1024} KB)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    stage(args.src, args.out)


if __name__ == "__main__":
    main()
