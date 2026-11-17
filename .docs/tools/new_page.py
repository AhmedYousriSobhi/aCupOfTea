#!/usr/bin/env python3
"""Create a new page: file name, folder, tags, front matter, index link, sidebar.

Run with no arguments and answer the questions:

  python3 .docs/tools/new_page.py

Or pass the answers as options (anything missing is still asked):

  python3 .docs/tools/new_page.py --title "Attention in Transformers" \
      --folder fields/deep-learning/concepts --tags transformers,attention \
      --summary "How attention lets a model weigh every token." --yes

It never overwrites a file and never creates a folder without asking. Only the
standard library is needed.

A page you wrote by hand gets the same front matter and index link without
touching its text:

  python3 .docs/tools/new_page.py --adopt fields/devops/kubernetes/my-page.md

and later its metadata can be changed (Enter keeps a value, - clears it; options skip the questions):

  python3 .docs/tools/new_page.py --update fields/devops/kubernetes/my-page.md --tags kubernetes,gpu

Reading time is not asked: the site computes it from the text (200 words a
minute, code excluded), so it never goes stale. Once the page is written, check
it and see its reading time and what is still missing:

  python3 .docs/tools/new_page.py --check fields/deep-learning/concepts/attention.md
"""
import argparse
import difflib
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import page_scaffold as sc  # noqa: E402
from page_scaffold import *  # noqa: F401,F403,E402  (new_page.<name> stays the public entry point)
from page_index import *  # noqa: F401,F403,E402
from page_prompts import *  # noqa: F401,F403,E402


def locate_page(given, flag):
    """(full path, repo-relative path) of a content page named on the command line, or exit with why not."""
    full = os.path.abspath(given if os.path.exists(given) else os.path.join(sc.ROOT, given))
    rel = os.path.relpath(full, sc.ROOT).replace(os.sep, "/")
    if not os.path.isfile(full):
        sys.exit("error: no page at %s" % given)
    if rel.startswith("../") or rel.split("/")[0].startswith(".") or "/" not in rel:
        sys.exit("error: %s is not a content page inside a content folder" % rel)
    if not rel.endswith(".md") or os.path.basename(rel) == "README.md":
        sys.exit("error: %s is for a .md content page; README.md files are folder indexes" % flag)
    if any(rel.startswith(sub + "/") for sub in submodules()):
        sys.exit("error: %s is inside a git submodule" % rel)
    return full, rel


def adopt(args, ask):
    """Add front matter to a page written by hand. The body is never touched."""
    if args.title or args.folder or args.name:
        sys.exit("error: --adopt takes the title from the page's heading and the folder from its path; "
                 "drop --title, --folder and --name")
    full, rel = locate_page(args.adopt, "--adopt")
    with open(full, "rb") as fh:
        text = fh.read().decode("utf-8")
    bom, text = ("\ufeff", text[1:]) if text.startswith("\ufeff") else ("", text)
    m = re.match(r"---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
    existing = m.group(1).splitlines() if m else []
    rest = text[m.end():] if m else text
    have = key_blocks(existing)
    if re.match(r"---[ \t]*\r?\n", text) and not m:
        sys.exit("error: %s starts with '---' but its front matter is not closed; fix that by hand "
                 "(nothing was changed)" % rel)
    title = body_h1(rest)
    if not title:
        sys.exit("error: %s has no '# ' heading to take the title from" % rel)

    folder, name = os.path.dirname(rel), os.path.basename(rel)[:-3]
    summary = ""
    if "summary" not in have:
        summary = args.summary if args.summary is not None else ask.text("Summary (one line, optional)", required=False)
        summary = " ".join(summary.split())
        if len(summary) > 200:
            sys.exit("error: keep the summary under 200 characters")
    folders = scan()
    print("\nAdopting %s  (title: \"%s\")" % (rel, title))
    if have:
        print("Keeping what the front matter already has: %s" % ", ".join(have))
    meta = ask_metadata(args, ask, title, folder, folders, have)
    page_id = name if name not in meta["ids"] else slug(folder.split("/")[-1] + "-" + name)
    first = text.find("\n")
    eol = "\r\n" if first > 0 and text[first - 1] == "\r" else "\n"
    added = front_matter_lines(page_id, title, summary, meta, note="sidebar_label" not in have)
    # a page that had no front matter gets a blank line after it; one that had keeps its own
    block = eol.join(merge_front_matter(existing, added, ("title",) if m else ())) + eol + ("" if m else eol)
    if m and not [k for k in key_blocks(added) if k not in have and k != "title"]:
        sys.exit("Nothing to add: %s already has all the fields asked for." % rel)

    if args.dry_run:
        print("\n--- %s (front matter after the change; the page text is unchanged) ---\n%s" % (rel, block))
        report_new(meta)
        return
    tmp = full + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write((bom + block + rest).encode("utf-8"))
    os.replace(tmp, full)                 # all or nothing
    print("\n%s front matter to %s (the page text is unchanged)" % ("Completed" if m else "Added", rel))
    save_taxonomy(meta)
    if listed_in_readme(folder, name):
        print("Already listed in %s/README.md" % folder)
    else:
        print(link_in_readme(folder, rel, title, summary))
    regenerate_navigation()
    print()
    check_page(rel)


def update(args, ask):
    """Change the summary, kind, subjects, tags, level or relations of a page that has front matter.
    Fields not given as options are asked (Enter keeps the current value, - clears it) when run by hand."""
    if args.title or args.folder or args.name:
        sys.exit("error: --update changes the metadata of an existing page; drop --title, --folder and --name")
    full, rel = locate_page(args.update, "--update")
    with open(full, "rb") as fh:
        text = fh.read().decode("utf-8")
    bom, text = ("\ufeff", text[1:]) if text.startswith("\ufeff") else ("", text)
    m = re.match(r"---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
    if not m:
        sys.exit("error: %s has no front matter; use --adopt to add it" % rel)
    existing, rest = m.group(1).splitlines(), text[m.end():]
    cur = parse_front(existing)
    folder, name = os.path.dirname(rel), os.path.basename(rel)[:-3]
    title = cur.get("title") or body_h1(rest) or name
    folders = scan()
    ids = existing_ids(folders)
    asked = ask.interactive and not ask.yes
    show = lambda v: ", ".join(v) if isinstance(v, list) else (v or "")
    print("\nUpdating %s  (title: \"%s\")" % (rel, title))
    changed, meta = set(), {"types": [], "domains": [], "tags": [], "level": "", "prereqs": [], "related": [],
                            "new_tags": {}, "new_domains": {}, "new_types": {}, "ids": ids}
    type_cur = cur.get("type", [])
    type_cur = type_cur if isinstance(type_cur, list) else [type_cur]

    def given(opt):
        return opt is not None or asked

    # each field: from the option, else asked with the current value as the default, else kept as it is
    summary = cur.get("summary", "")
    if given(args.summary):
        raw = args.summary if args.summary is not None else ask.text("Summary (one line)", summary, required=False)
        raw = "" if raw.strip() == "-" else " ".join(raw.split())
        if len(raw) > 200:
            sys.exit("error: keep the summary under 200 characters")
        if raw != summary:
            summary, _ = raw, changed.add("summary")
    types = type_cur
    if given(args.type):
        got, meta["new_types"] = choose_type(args, ask, folder, folders, default=show(type_cur))
        if got != type_cur:
            types, _ = got, changed.add("types")
    domains = cur.get("domains", [])
    if given(args.domains):
        got, meta["new_domains"] = choose_domains(args, ask, folder, folders, title, default=show(domains))
        if got != domains:
            domains, _ = got, changed.add("domains")
    tags = cur.get("tags", [])
    if given(args.tags):
        got, meta["new_tags"] = choose_tags(args, ask, title, load_tags(), default=show(tags))
        if got != tags:
            tags, _ = got, changed.add("tags")
    level = cur.get("level", "")

    def parse_level(raw):
        raw = raw.strip().lower()
        raw = "" if raw == "-" else raw
        if raw and raw not in LEVELS:
            raise Invalid("level must be one of %s" % ", ".join(LEVELS))
        return raw
    if given(args.level):
        got = resolve(ask, args.level, parse_level, lambda: ask.text("Level (%s)" % "/".join(LEVELS), level, required=False))
        if got != level:
            level, _ = got, changed.add("level")
    prereqs, related = cur.get("prerequisites", []), cur.get("related", [])
    for label, opt, now, key in (("Prerequisites", args.prerequisites, prereqs, "prerequisites"),
                                 ("Related", args.related, related, "related")):
        if given(opt):
            got = resolve(ask, opt, lambda raw: [] if raw.strip() == "-" else page_ids(raw, ids - {cur.get("id")}, label.lower()),
                          lambda: ask.text(label, show(now), required=False))
            if got != now:
                changed.add("relations")
                if key == "prerequisites":
                    prereqs = got
                else:
                    related = got
    related = [r for r in related if r not in prereqs]
    if not changed:
        sys.exit("Nothing to change in %s." % rel)

    meta.update(types=types, domains=domains, tags=tags, level=level, prereqs=prereqs, related=related)
    page_id = cur.get("id") or (name if name not in ids else slug(folder.split("/")[-1] + "-" + name))
    fresh = key_blocks(front_matter_lines(page_id, title, summary, meta, note=False))
    have = key_blocks(existing)
    for group in changed:
        for key in UPDATE_KEYS[group]:
            if key in fresh:
                have[key] = fresh[key]
            else:
                have.pop(key, None)         # cleared
    if "relations" in changed and "relations" in fresh and "id" not in have:
        have["id"] = fresh["id"]            # relations need an id
    order = [k for k in FM_ORDER if k in have] + [k for k in have if k not in FM_ORDER]
    first = text.find("\n")
    eol = "\r\n" if first > 0 and text[first - 1] == "\r" else "\n"
    block = eol.join(["---"] + [l for k in order for l in have[k]] + ["---"]) + eol
    new_text = block + rest
    old_block = text[:m.end()]
    if args.dry_run:
        import difflib as _d
        print("\n--- %s (front matter changes; the page text is unchanged) ---" % rel)
        print("\n".join(l for l in _d.unified_diff(old_block.splitlines(), block.splitlines(), "before", "after", lineterm="", n=0)
                        if not l.startswith(("---", "+++", "@@"))) or "(no visible change)")
        report_new(meta)
        return
    tmp = full + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write((bom + new_text).encode("utf-8"))
    os.replace(tmp, full)
    print("\nUpdated front matter of %s (the page text is unchanged): %s" % (rel, ", ".join(sorted(changed))))
    save_taxonomy(meta)
    print("Next: python3 .docs/tools/page_doctor.py (it also checks that the generated indexes are current)")


def main(argv=None):
    p = argparse.ArgumentParser(description="Create a new page with front matter, an index link and a fresh sidebar.")
    p.add_argument("--title")
    p.add_argument("--summary", help="one line, shown in search results")
    p.add_argument("--folder", help="e.g. fields/deep-learning/concepts")
    p.add_argument("--name", help="file name without .md (default: from the title)")
    p.add_argument("--tags", help="comma separated, e.g. transformers,attention")
    p.add_argument("--level", help="beginner, intermediate or advanced; beginner pages show under 'Beginner friendly' (--update: - clears it)")
    p.add_argument("--type", help="one or two of concept, guide, reference, note, problem, project, experiment, comma separated")
    p.add_argument("--domains", help="up to three related subjects from taxonomy.yaml, comma separated, e.g. deep-learning")
    p.add_argument("--prerequisites", help="comma separated page ids to read first, e.g. deep-learning-basics")
    p.add_argument("--related", help="comma separated page ids to see also")
    p.add_argument("--check", metavar="PAGE", help="report a written page's reading time and what is missing")
    p.add_argument("--adopt", metavar="PAGE", help="add front matter and an index link to a page you wrote by hand")
    p.add_argument("--create-folder", action="store_true", help="create the folder if it does not exist, without asking")
    p.add_argument("--new-domain", action="append", default=[], metavar="KEY=DESCRIPTION", type=key_value,
                   help="confirm a new subject and add it to taxonomy.yaml (repeatable)")
    p.add_argument("--new-type", action="append", default=[], metavar="KEY=DESCRIPTION", type=key_value,
                   help="confirm a new kind of page and add it to taxonomy.yaml (repeatable)")
    p.add_argument("--new-tag", action="append", default=[], metavar="KEY[=LABEL]", type=key_value,
                   help="confirm a new tag and add it to taxonomy.yaml (repeatable)")
    p.add_argument("--gui", action="store_true", help="open the page form in your browser (local only)")
    p.add_argument("--update", metavar="PAGE", help="change the summary, kind, subjects, tags, level or relations of a page that has front matter")
    p.add_argument("--yes", action="store_true", help="accept defaults and suggestions without asking")
    p.add_argument("--dry-run", action="store_true", help="show what would be written, change nothing")
    args = p.parse_args(argv)
    if args.gui:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import page_gui
        return page_gui.serve()
    if args.check:
        return 1 if check_page(args.check) else 0
    ask = Asker(args.yes)
    if args.adopt:
        return adopt(args, ask)
    if args.update:
        return update(args, ask)

    title = (args.title or ask.text("Title")).strip()
    if not title:
        sys.exit("error: a title is required")
    summary = args.summary if args.summary is not None else ask.text("Summary (one line, optional)", required=False)
    summary = " ".join(summary.split())
    if len(summary) > 200:
        sys.exit("error: keep the summary under 200 characters")

    folders = scan()
    warn_similar(title, folders, ask)
    folder = choose_folder(args, ask, title, folders)

    name = slug(args.name or ask.text("File name", slug(title)))
    if not name:
        sys.exit("error: empty file name")
    page_rel = "%s/%s.md" % (folder, name)
    if os.path.exists(os.path.join(sc.ROOT, page_rel)):
        sys.exit("error: %s already exists" % page_rel)
    new_folder = not os.path.isdir(os.path.join(sc.ROOT, folder))

    meta = ask_metadata(args, ask, title, folder, folders)
    page_id = name if name not in meta["ids"] else slug(folder.split("/")[-1] + "-" + name)
    fm = front_matter_lines(page_id, title, summary, meta)
    intro = summary or "<!-- One or two sentences: what will the reader learn? -->"
    content = "\n".join(fm) + "\n\n" + BODY.format(title=title, intro=intro)

    if args.dry_run:
        print("\n--- %s ---\n%s" % (page_rel, content))
        report_new(meta)
        return

    full = os.path.join(sc.ROOT, page_rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print("\nCreated  %s" % page_rel)
    save_taxonomy(meta)
    if new_folder and not os.path.exists(os.path.join(sc.ROOT, folder, "README.md")):
        print("\n".join(create_folder_readme(folder, page_rel, title, summary)))
    else:
        print(link_in_readme(folder, page_rel, title, summary))
    regenerate_navigation()
    print("\nNext: write the page. The site shows its reading time from the text; to see it")
    print("and what is still missing, run:  python3 .docs/tools/new_page.py --check %s" % page_rel)
    print("Then commit it on a branch from dev.")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nStopped: nothing more was changed.")
