"""Folder index links for new pages: the README table row or bullet, a new folder README,
and regenerating the sidebar and navbar. Part of new_page.py (split for size).
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
from page_scaffold import *  # noqa: F401,F403,E402


def index_table(lines):
    """(start, end, columns) of the table in a README that lists pages: the File/Directory one, else the
    first table whose rows start with a link. Rows are lines[start:end]."""
    found = []
    for i in range(len(lines) - 1):
        if lines[i].lstrip().startswith("|") and SEPARATOR.match(lines[i + 1]):
            start = end = i + 2
            while end < len(lines) and lines[end].lstrip().startswith("|"):
                end += 1
            linked = any(re.match(r"^\|\s*\[", l) for l in lines[start:end])
            named = bool(TABLE_HEAD.match(lines[i].lstrip()))
            if named or linked:
                found.append((not named, start, end, lines[i].strip().strip("|").count("|") + 1))
    if not found:
        return None
    _, start, end, cols = min(found)
    return start, end, cols


def add_table_row(lines, stem, link, description):
    """Insert a row for `stem` into the README's page table (alphabetical when the table is). True if done."""
    table = index_table(lines)
    if not table:
        return False
    start, end, cols = table
    if not lines[end - 1].endswith("\n"):
        lines[end - 1] += "\n"
    row = "| [%s](%s) | %s |%s\n" % (stem, link, description, " |" * max(0, cols - 2)) if cols > 1 else "| [%s](%s) |\n" % (stem, link)
    keys = [re.sub(r"^\|\s*\[([^\]]*)\].*", r"\1", l).lower() for l in lines[start:end]]
    pos = end
    if keys == sorted(keys):
        pos = start + sum(1 for k in keys if k < stem)
    lines.insert(pos, row)
    return True


def link_in_readme(folder, page_rel, title, summary):
    """Add the page to the folder README's index: a table of pages (File/Directory, or any table whose
    rows start with a link), or failing that the last bullet list of links. Returns a message."""
    readme = os.path.join(sc.ROOT, folder, "README.md")
    stem = os.path.basename(page_rel)[:-3]
    row = "| [%s](/%s) | %s |" % (stem, page_rel, summary or title)
    bullet = "- [%s](/%s)" % (title, page_rel)
    if not os.path.exists(readme):
        return "No README.md in %s; the sidebar still lists the page." % folder
    lines = read(readme).splitlines(keepends=True)
    if not add_table_row(lines, stem, "/" + page_rel, summary or title):
        last = None
        in_code = False
        for i, line in enumerate(lines):
            if line.lstrip().startswith("```"):
                in_code = not in_code
            if not in_code and BULLET_LINK.match(line):
                last = i
        if last is None:
            return "Add this line to %s/README.md yourself:\n  %s" % (folder, row)
        if not lines[last].endswith("\n"):
            lines[last] += "\n"
        lines.insert(last + 1, bullet + "\n")
    with open(readme, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return "Linked   in %s/README.md" % folder


def create_folder_readme(folder, page_rel, title, summary):
    """A README for a folder this run created: heading, a purpose line to fill in, and the contents table
    holding the page. Also lists the folder in the parent's README table when that has one. Returns messages."""
    heading = " ".join(w.capitalize() for w in os.path.basename(folder).split("-"))
    stem = os.path.basename(page_rel)[:-3]
    text = ("# %s\n\n<!-- One line: what belongs in this folder. -->\n\n## Contents\n\n"
            "| File | Description |\n|---|---|\n| [%s](/%s) | %s |\n" % (heading, stem, page_rel, summary or title))
    with open(os.path.join(sc.ROOT, folder, "README.md"), "w", encoding="utf-8") as f:
        f.write(text)
    out = ["Created  %s/README.md (fill in its purpose line)" % folder]
    parent = os.path.join(sc.ROOT, os.path.dirname(folder), "README.md")
    if os.path.dirname(folder) and os.path.exists(parent):
        lines = read(parent).splitlines(keepends=True)
        name = os.path.basename(folder)
        if add_table_row(lines, name, "/%s/README.md" % folder, heading):
            with open(parent, "w", encoding="utf-8") as f:
                f.writelines(lines)
            out.append("Listed   %s in %s/README.md (edit its description)" % (name, os.path.dirname(folder)))
    return out


def regenerate_navigation():
    docs = os.path.join(sc.ROOT, ".docs")
    for script in ("gen_sidebar.sh", "gen_navbar.sh"):
        subprocess.run(["bash", script], cwd=docs, check=True, stdout=subprocess.DEVNULL)
    print("Updated  .docs/_sidebar.md and .docs/_navbar.md")
    # The indexes refuse to build while the validator reports errors; say so instead of failing the page.
    done = subprocess.run([sys.executable, os.path.join(sc.ROOT, ".docs", "tools", "generate_index.py")],
                          cwd=sc.ROOT, capture_output=True, text=True)
    if done.returncode == 0:
        print("Updated  .docs/generated")
    else:
        print("Skipped  .docs/generated (generate_index.py refused; run check_all.py --fix)")


def listed_in_readme(folder, stem):
    readme = os.path.join(sc.ROOT, folder, "README.md")
    return os.path.exists(readme) and bool(
        re.search(r"\]\((?:[^)\s]*/)?%s\.md\)" % re.escape(stem), read(readme)))
