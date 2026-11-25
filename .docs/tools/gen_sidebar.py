#!/usr/bin/env python3
"""Generate .docs/_sidebar.md from the folder tree (replaces the old bash generator).

Never hand-edit the output. `.docs/gen_sidebar.sh` runs this script, so CI, the
pre-commit hook and `check_all.py` keep working unchanged.

Rules (unchanged from the bash version):
  * Home, an Explore group (when the generated pages exist), then the folder tree,
    then an "About this site" group.
  * In a folder: a page titled Overview first, then pages by `order` (front matter),
    then the rest in the order the folder README links them, then alphabetically.
  * A page's label is its `sidebar_label`, else the text after the last hyphen of its
    `# ` heading. A folder's group name is `sidebar_group` on its README, else the text
    before the last hyphen of the README heading; the group heading links to the README.
  * Git submodules are listed as external links; folders without pages are skipped.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pagemodel import Page, title_case_words  # noqa: E402

DOCS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(DOCS)
OUTPUT = os.path.join(DOCS, "_sidebar.md")
EXCLUDE_DIRS = re.compile(r"^(\.git|\.github|node_modules|\.docs|docs|_site)$")
EXCLUDE_FILES = re.compile(r"_sidebar.md|_navbar.md|index.html|CLAUDE.md")  # unanchored, as before
LINK_RE = re.compile(r"\]\(([^)\n]*)\)")
CONTRIBUTING = "https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/.github/CONTRIBUTING.md"


def readme_ranks(root, rel):
    """{path relative to the root: position} for the targets a folder README links, first link first."""
    readme = os.path.join(root, rel, "README.md") if rel else os.path.join(root, "README.md")
    rank = {}
    try:
        with open(readme, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return rank
    for m in LINK_RE.finditer(text):
        t = re.sub(r"[#?].*$", "", m.group(1))
        t = re.sub(r"\s.*$", "", t)
        if t == "" or "://" in t:
            continue
        if t.startswith("/"):
            t = t[1:]
        elif rel:
            t = rel + "/" + t
        t = re.sub(r"^\./", "", t)
        t = re.sub(r"/$", "", t)
        rank.setdefault(t, len(rank) + 1)
    return rank


def ordered_names(root, rel):
    """Entries of a folder in the order its README links them, then the rest alphabetically (bytewise)."""
    here = os.path.join(root, rel) if rel else root
    names = sorted((n for n in os.listdir(here) if not n.startswith(".")), key=os.fsencode)
    rank = readme_ranks(root, rel)

    def r(name):
        key = f"{rel}/{name}" if rel else name
        if key in rank:
            return rank[key]
        if key + "/README.md" in rank:
            return rank[key + "/README.md"]
        return 1000000

    return sorted(names, key=r)  # stable: equal ranks keep the alphabetical order


def has_pages(folder):
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if any(f.endswith(".md") and not f.startswith(".") for f in filenames):
            return True
    return False


def submodules(root):
    """{path: url without .git} from .gitmodules ({} without git or the file)."""
    gm = os.path.join(root, ".gitmodules")
    if not os.path.exists(gm):
        return {}
    try:
        out = subprocess.run(["git", "config", "-f", gm, "--list"], capture_output=True, text=True).stdout
    except OSError:
        return {}
    paths, urls = {}, {}
    for line in out.splitlines():
        key, _, value = line.partition("=")
        if key.startswith("submodule.") and key.endswith(".path"):
            paths[key[len("submodule."):-len(".path")]] = value
        elif key.startswith("submodule.") and key.endswith(".url"):
            urls[key[len("submodule."):-len(".url")]] = value
    return {p: re.sub(r"\.git$", "", urls[n]) for n, p in paths.items() if n in urls}


def walk(root, rel, indent, subs, out):
    here = os.path.join(root, rel) if rel else root
    folders, files, overview = [], [], None
    for name in ordered_names(root, rel):
        if EXCLUDE_DIRS.search(name) or EXCLUDE_FILES.search(name):
            continue
        if not rel and name in ("README.md", "SPEC.md"):  # Home and the About group
            continue
        path = os.path.join(here, name)
        if os.path.isdir(path):
            folders.append(name)
        elif name == "README.md":
            continue  # linked from the folder heading
        elif name.endswith(".md"):
            page = Page(path)
            label = page.menu_label()
            entry = f"{indent}* [{label}]({rel + '/' if rel else ''}{name})"
            if label.lower() == "overview":
                overview = entry
            else:
                order = page.order
                files.append((1_000_000 + order if order is not None else 2_000_000, entry))
    if overview:
        out.append(overview)
    out.extend(e for _, e in sorted(files, key=lambda t: t[0]))  # stable on the key only

    for name in folders:
        sub_rel = f"{rel}/{name}" if rel else name
        folder = os.path.join(root, sub_rel)
        if sub_rel in subs:
            out.append(f"{indent}* [{title_case_words(name)} ↗]({subs[sub_rel]})")
            continue
        if not has_pages(folder):
            continue
        readme = os.path.join(folder, "README.md")
        has_readme = os.path.isfile(readme)
        group = Page(readme).menu_group(name) if has_readme else title_case_words(name)
        out.append(f"{indent}* [**{group}**]({sub_rel}/README.md)" if has_readme else f"{indent}* **{group}**")
        walk(root, sub_rel, "  " + indent, subs, out)


def build(root=ROOT, docs=DOCS):
    out = ["* [Home](README.md)"]
    gen = os.path.join(docs, "generated", "explore")
    if os.path.isfile(os.path.join(gen, "domains.md")) and os.path.isfile(os.path.join(gen, "tags.md")):
        out.append("* **Explore**")
        if os.path.isfile(os.path.join(gen, "start-here.md")):
            out.append("  * [Start here](.docs/generated/explore/start-here.md)")
        out.append("  * [Domains](.docs/generated/explore/domains.md)")
        out.append("  * [Tags](.docs/generated/explore/tags.md)")
    walk(root, "", "", submodules(root), out)
    if os.path.isfile(os.path.join(root, "SPEC.md")):
        out += ["* **About this site**", "  * [Repository Specification](SPEC.md)",
                f"  * [Contributing guide ↗]({CONTRIBUTING})"]
    return "\n".join(out) + "\n"


def main():
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(build())
    print("Sidebar updated: Logic applied for single-word headers and dash-separated titles.")


if __name__ == "__main__":
    main()
