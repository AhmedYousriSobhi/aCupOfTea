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
"""
import argparse
import difflib
import math
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAXONOMY = os.path.join(ROOT, ".docs", "metadata", "taxonomy.yaml")
SKIP_DIRS = {"__pycache__", "node_modules", "_site", "docs", "data"}
STOP = set("a an and are as at be by for from how in into is it of on or the to vs what why with".split())
MAX_TAGS = 5

BODY = """# {title}

{intro}

## Why it matters

<!-- The problem this solves, or where you ran into it. -->

## How it works

<!-- The idea, step by step. Diagrams and examples help. -->

## Example

<!-- Code, commands or a worked case from real experience. -->

## Takeaways

<!-- Two or three lines worth remembering. -->

## References

<!-- Links you used or recommend. -->
"""


# ---------- small helpers ----------

def slug(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def words(text):
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP or len(w) < 2:
            continue
        out.add(w[:-1] if len(w) > 3 and w.endswith("s") else w)
    return out


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def first_h1(path):
    for line in read(path).splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def sidebar_label(h1):
    # Mirrors gen_sidebar.sh: the label is the text after the last hyphen.
    return h1.rsplit("-", 1)[-1].strip() if "-" in h1 else h1


def submodules():
    path = os.path.join(ROOT, ".gitmodules")
    if not os.path.exists(path):
        return set()
    return set(re.findall(r"^\s*path\s*=\s*(\S+)", read(path), re.M))


def scan():
    """Return {folder: [(rel_path, h1), ...]} for every folder holding pages."""
    subs = submodules()
    folders = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT).replace(os.sep, "/")
        dirnames[:] = sorted(d for d in dirnames
                             if not d.startswith(".") and d not in SKIP_DIRS
                             and (rel_dir + "/" + d).lstrip("./") not in subs)
        if rel_dir == ".":
            continue
        pages = [(rel_dir + "/" + f, first_h1(os.path.join(dirpath, f)))
                 for f in sorted(filenames) if f.endswith(".md")]
        if pages:
            folders[rel_dir] = pages
    return folders


def existing_ids(folders):
    ids = set()
    for pages in folders.values():
        for rel, _ in pages:
            m = re.match(r"---\n(.*?)\n---\n", read(os.path.join(ROOT, rel)), re.S)
            if m:
                ids.update(re.findall(r"^id:\s*(\S+)", m.group(1), re.M))
    return ids


# ---------- tags (taxonomy.yaml, read without a YAML library) ----------

def load_tags():
    tags, current, in_tags = {}, None, False
    for line in read(TAXONOMY).splitlines():
        if re.match(r"^\S", line):
            in_tags = line.rstrip() == "tags:"
            continue
        if not in_tags:
            continue
        m = re.match(r"^  ([a-z0-9-]+):\s*$", line)
        if m:
            current = m.group(1)
            tags[current] = current
            continue
        m = re.match(r"^    label:\s*(.+?)\s*$", line)
        if m and current:
            tags[current] = m.group(1).strip("\"'")
    return tags


def add_tags(new):
    """Insert new tags into the tags block of taxonomy.yaml, keeping it sorted."""
    lines = read(TAXONOMY).splitlines(keepends=True)
    start = next(i for i, l in enumerate(lines) if l.rstrip() == "tags:")
    end = start + 1
    while end < len(lines) and (not re.match(r"^\S", lines[end])):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1                       # keep blank lines after the block outside it
    for key, label in sorted(new.items()):
        pos = end
        for i in range(start + 1, end):
            m = re.match(r"^  ([a-z0-9-]+):\s*$", lines[i])
            if m and m.group(1) > key:
                pos = i
                break
        lines[pos:pos] = ["  %s:\n" % key, "    label: %s\n" % label]
        end += 2
    with open(TAXONOMY, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ---------- prompts ----------

class Asker:
    def __init__(self, yes):
        self.yes = yes
        self.interactive = sys.stdin.isatty()

    def text(self, prompt, default="", required=True):
        if self.yes or not self.interactive:
            if default or not required:
                return default
            sys.exit("error: %s is required (pass it as an option)" % prompt.split(" (")[0].lower())
        hint = " [%s]" % default if default else ""
        value = input("%s%s: " % (prompt, hint)).strip()
        return value or default

    def confirm(self, prompt, default=True):
        if self.yes or not self.interactive:
            return default
        hint = "[Y/n]" if default else "[y/N]"
        value = input("%s %s " % (prompt, hint)).strip().lower()
        return default if not value else value.startswith("y")


def complete_with(options):
    try:
        import readline
    except ImportError:
        return
    def completer(text, state):
        head, _, last = text.rpartition(",")
        last = last.lstrip()
        hits = [o for o in options if o.startswith(last)]
        prefix = (head + ", ") if head else ""
        return prefix + hits[state] if state < len(hits) else None
    readline.set_completer_delims("")
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")


# ---------- steps ----------

def page_words(rel, h1):
    return words(sidebar_label(h1)) | words(os.path.basename(rel)[:-3])


def suggest_folders(title, folders, limit=5):
    """Rank folders by title words found in their path and page titles.

    Rare words count more than common ones ("slurm" beats "job"), so a folder
    full of matching pages wins over one that only shares a generic word.
    """
    want = words(title)
    bags = {}
    for folder, pages in folders.items():
        path = words(folder.replace("/", " "))
        hits = {}
        for rel, h1 in pages:
            found = page_words(rel, h1) | words(h1)
            if os.path.basename(rel) == "README.md":
                found |= words(read(os.path.join(ROOT, rel)))   # the folder's own description
            for w in found:
                hits[w] = hits.get(w, 0) + 1
        bags[folder] = (path, hits)
    df = {w: sum(1 for path, hits in bags.values() if w in path or w in hits) for w in want}
    scored = []
    for folder, (path, hits) in bags.items():
        score = sum(math.log((1 + len(bags)) / (1 + df[w])) * (2 * (w in path) + min(3, hits.get(w, 0)))
                    for w in want)
        if score > 0:
            scored.append((-score, folder.count("/"), folder))
    return [f for _, _, f in sorted(scored)[:limit]]


def folder_problem(folder, folders):
    if not folder:
        return "no folder chosen"
    if folder.split("/")[0] not in {f.split("/")[0] for f in folders}:
        return "%s is not under an existing top-level folder" % folder
    bad = [p for p in folder.split("/") if p != slug(p)]
    if bad and not os.path.isdir(os.path.join(ROOT, folder)):
        return "new folder names must be lowercase-kebab-case: %s" % ", ".join(bad)
    return ""


def pick(options, answer):
    if answer.isdigit() and 0 < int(answer) <= len(options):
        return options[int(answer) - 1]
    return answer.strip().strip("/")


def subfolders(folder, folders):
    depth = folder.count("/") + 1
    return sorted({"/".join(f.split("/")[:depth + 1]) for f in folders
                   if f.startswith(folder + "/")})


def choose_folder(args, ask, title, folders):
    if args.folder:
        folder = args.folder.strip("/")
        problem = folder_problem(folder, folders)
        if problem:
            sys.exit("error: " + problem)
    else:
        hits = suggest_folders(title, folders)
        options = hits or sorted({f.split("/")[0] for f in folders})
        print("\nWhere does it go?" + ("  (closest folders first)" if hits else ""))
        for i, f in enumerate(options, 1):
            print("  %d) %s" % (i, f))
        print("  or type a folder path (Tab completes)")
        while True:
            complete_with(sorted(folders))
            folder = pick(options, ask.text("Folder", "1" if hits and ask.yes else ""))
            problem = folder_problem(folder, folders)
            if not problem:
                break
            if not ask.interactive or ask.yes:
                sys.exit("error: " + problem)
            print("  " + problem + ", try again")
        # Offer to go deeper when the chosen folder has subfolders.
        while not ask.yes and subfolders(folder, folders):
            children = subfolders(folder, folders)
            print("\n%s has subfolders:" % folder)
            print("  0) put it here")
            for i, f in enumerate(children, 1):
                print("  %d) %s" % (i, f))
            answer = ask.text("Choice", "0")
            if answer == "0":
                break
            choice = pick(children, answer)
            if folder_problem(choice, folders):
                print("  not a valid choice, try again")
                continue
            folder = choice
    if not os.path.isdir(os.path.join(ROOT, folder)):
        if not ask.confirm("%s does not exist. Create it?" % folder, default=False):
            sys.exit("Stopped: no folder created.")
    return folder


def warn_similar(title, folders, ask):
    want = words(title)
    norm = slug(title)
    hits = []
    for pages in folders.values():
        for rel, h1 in pages:
            if os.path.basename(rel) == "README.md":
                continue
            have = page_words(rel, h1)
            covered = len(want & have) / max(1, len(want))
            jaccard = len(want & have) / max(1, len(want | have))
            ratio = max(difflib.SequenceMatcher(None, norm, slug(sidebar_label(h1))).ratio(),
                        difflib.SequenceMatcher(None, norm, os.path.basename(rel)[:-3]).ratio())
            score = max(jaccard, ratio, covered if len(want) >= 2 else 0)
            if jaccard >= 0.5 or ratio >= 0.8 or (len(want) >= 2 and covered >= 0.75):
                hits.append((-score, rel, h1))
    if not hits:
        return
    print("\nSimilar pages already exist:")
    for _, rel, h1 in sorted(hits)[:3]:
        print("  - %s  \"%s\"" % (rel, h1))
    if not ask.confirm("Continue with a new page?"):
        sys.exit("Stopped: nothing created.")


def choose_tags(args, ask, title, known):
    if args.tags is not None:
        raw = args.tags
    else:
        want = words(title)
        hint = [k for k, label in sorted(known.items()) if want & (words(k) | words(label))]
        print("\nTags (comma separated, Tab completes). Known: %s" % ", ".join(sorted(known)))
        complete_with(sorted(known))
        raw = ask.text("Tags", ", ".join(hint), required=False)
    tags = []
    for t in raw.split(","):
        t = slug(t)
        if t and t not in tags:
            tags.append(t)
    if len(tags) > MAX_TAGS:
        sys.exit("error: at most %d tags per page" % MAX_TAGS)
    new = {}
    for t in [t for t in tags if t not in known]:
        label = " ".join(w.capitalize() for w in t.split("-"))
        print("\"%s\" is a new tag (label \"%s\")." % (t, label))
        if ask.confirm("Add it to the tag list?", default=False):
            new[t] = label
        else:
            tags.remove(t)
    return tags, new


def yaml_value(v):
    if re.search(r"[:#\[\]{},&*!|>'\"%@`]|^\s|\s$|^[-?]", v):
        return '"%s"' % v.replace("\\", "\\\\").replace('"', '\\"')
    return v


def link_in_readme(folder, page_rel, title, summary):
    """Add a row to the folder README's file table. Returns a message."""
    readme = os.path.join(ROOT, folder, "README.md")
    row = "| [%s](/%s) | %s |" % (os.path.basename(page_rel)[:-3], page_rel, summary or title)
    if not os.path.exists(readme):
        return "No README.md in %s; the sidebar still lists the page." % folder
    lines = read(readme).splitlines(keepends=True)
    for i, line in enumerate(lines):
        if re.match(r"^\|\s*File(/Directory)?\s*\|", line):
            start = end = i + 2
            while end < len(lines) and lines[end].startswith("|"):
                end += 1
            if not lines[end - 1].endswith("\n"):
                lines[end - 1] += "\n"
            # Keep the table's order when it is alphabetical; otherwise append.
            keys = [re.sub(r"^\|\s*\[([^\]]*)\].*", r"\1", l).lower() for l in lines[start:end]]
            pos = end
            if keys == sorted(keys):
                pos = start + sum(1 for k in keys if k < os.path.basename(page_rel)[:-3])
            lines.insert(pos, row + "\n")
            with open(readme, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return "Linked   in %s/README.md" % folder
    return "Add this line to %s/README.md yourself:\n  %s" % (folder, row)


def main():
    p = argparse.ArgumentParser(description="Create a new page with front matter, an index link and a fresh sidebar.")
    p.add_argument("--title")
    p.add_argument("--summary", help="one line, shown in search results")
    p.add_argument("--folder", help="e.g. fields/deep-learning/concepts")
    p.add_argument("--name", help="file name without .md (default: from the title)")
    p.add_argument("--tags", help="comma separated, e.g. transformers,attention")
    p.add_argument("--yes", action="store_true", help="accept defaults and suggestions without asking")
    p.add_argument("--dry-run", action="store_true", help="show what would be written, change nothing")
    args = p.parse_args()
    ask = Asker(args.yes)

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
    if os.path.exists(os.path.join(ROOT, page_rel)):
        sys.exit("error: %s already exists" % page_rel)

    tags, new_tags = choose_tags(args, ask, title, load_tags())

    page_id = name if name not in existing_ids(folders) else slug(folder.split("/")[-1] + "-" + name)
    fm = ["---", "id: %s" % page_id, "title: %s" % yaml_value(title)]
    label = sidebar_label(title)
    if label != title:
        print("\nNote: the sidebar shows the text after the last hyphen (\"%s\")." % label)
        print("      sidebar_label is set so the full title is used once labels are supported.")
        fm.append("sidebar_label: %s" % yaml_value(title))
    if summary:
        fm.append("summary: %s" % yaml_value(summary))
    if tags:
        fm.append("tags: [%s]" % ", ".join(tags))
    fm.append("---")
    intro = summary or "<!-- One or two sentences: what will the reader learn? -->"
    content = "\n".join(fm) + "\n\n" + BODY.format(title=title, intro=intro)

    if args.dry_run:
        print("\n--- %s ---\n%s" % (page_rel, content))
        if new_tags:
            print("New tags for taxonomy.yaml: %s" % ", ".join(new_tags))
        return

    full = os.path.join(ROOT, page_rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print("\nCreated  %s" % page_rel)
    if new_tags:
        add_tags(new_tags)
        print("Added    tags %s to .docs/metadata/taxonomy.yaml" % ", ".join(sorted(new_tags)))
    print(link_in_readme(folder, page_rel, title, summary))

    docs = os.path.join(ROOT, ".docs")
    for script in ("gen_sidebar.sh", "gen_navbar.sh"):
        subprocess.run(["bash", script], cwd=docs, check=True, stdout=subprocess.DEVNULL)
    print("Updated  .docs/_sidebar.md and .docs/_navbar.md")
    print("\nNext: write the page, then commit it on a branch from dev.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nStopped: nothing more was changed.")
