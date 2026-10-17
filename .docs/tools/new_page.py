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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAXONOMY = os.path.join(ROOT, ".docs", "metadata", "taxonomy.yaml")
SKIP_DIRS = {"__pycache__", "node_modules", "_site", "docs", "data"}
STOP = set("a an and are as at be by for from how in into is it of on or the to vs what why with".split())
MAX_TAGS = 5
MAX_DOMAINS = 2
MAX_TYPES = 2
LEVELS = ("beginner", "intermediate", "advanced")
WORDS_PER_MIN = 200     # same as generate_index.py
QUICK_MIN = 10          # "quick read" in Start here
FENCE_BLOCK = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.S | re.M)
TABLE_HEAD = re.compile(r"^\|\s*(File|Directory)(/(File|Directory))?\s*\|")
BULLET_LINK = re.compile(r"^[-*]\s+\[")

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


def load_section(name):
    """Keys of a top-level mapping in taxonomy.yaml (types, domains), in file order."""
    keys, inside = [], False
    for line in read(TAXONOMY).splitlines():
        if re.match(r"^\S", line):
            inside = line.split("#")[0].rstrip() == name + ":"
            continue
        m = inside and re.match(r"^  ([a-z0-9-]+):", line)
        if m:
            keys.append(m.group(1))
    return keys


def folder_defaults():
    """{folder: [domains]} from the folder_defaults block of taxonomy.yaml."""
    out, current, inside = {}, None, False
    for line in read(TAXONOMY).splitlines():
        if re.match(r"^\S", line):
            inside = line.split("#")[0].rstrip() == "folder_defaults:"
            continue
        if not inside:
            continue
        m = re.match(r"^  (\S+):\s*$", line)
        if m:
            current = m.group(1)
            out[current] = []
            continue
        m = re.match(r"^    -\s*([a-z0-9-]+)", line)
        if m and current:
            out[current].append(m.group(1))
    return out


def front_matter(rel):
    """{key: value} of a page's front matter (flat keys; [a, b] lists as lists)."""
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", read(os.path.join(ROOT, rel)), re.S)
    data, last = {}, None
    for line in (m.group(1).splitlines() if m else []):
        kv = re.match(r"^([a-z_]+):\s*(.*?)\s*$", line)
        item = re.match(r"^\s+-\s*(.+?)\s*$", line)
        if kv:
            last, v = kv.group(1), kv.group(2)
            data[last] = [x.strip() for x in v[1:-1].split(",") if x.strip()] if v.startswith("[") else v.strip("\"'")
        elif item and last and data.get(last) in ("", []):
            data[last] = []
        if item and last and isinstance(data.get(last), list):
            data[last].append(item.group(1).strip("\"'"))
    return data


def neighbours(folder, folders, key):
    """Counts of a front matter value among pages in the folder, else the nearest parent with any."""
    parts = folder.split("/")
    while parts:
        here = "/".join(parts)
        counts = {}
        for f, pages in folders.items():
            if f != here:
                continue
            for rel, _ in pages:
                v = front_matter(rel).get(key)
                # a value listed first counts a little more (the main subject comes first)
                for pos, x in enumerate(v if isinstance(v, list) else [v] if v else []):
                    counts[x] = counts.get(x, 0) + 1 + (0.5 if pos == 0 else 0)
        if counts:
            return sorted(counts, key=lambda x: (-counts[x], x))
        parts.pop()
    return []


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


def add_domains(new):
    """Append new domains ({key: (label, description)}) to the end of the domains block."""
    lines = read(TAXONOMY).splitlines(keepends=True)
    start = next(i for i, l in enumerate(lines) if l.split("#")[0].rstrip() == "domains:")
    end = start + 1
    while end < len(lines) and not re.match(r"^\S", lines[end]):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1                       # blank lines after the block stay outside it
    add = []
    for key, (label, description) in new.items():
        add += ["  %s:\n" % key, "    label: %s\n" % label, "    description: %s\n" % description]
    lines[end:end] = add
    with open(TAXONOMY, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ---------- prompts ----------

class Invalid(Exception):
    """A bad answer; the message says what is wrong."""


def resolve(ask, supplied, parse, prompt):
    """Get an answer and parse it. A bad option exits; a bad typed answer is asked again,
    so one typo does not throw away everything already answered."""
    if supplied is not None:
        try:
            return parse(supplied)
        except Invalid as e:
            sys.exit("error: %s" % e)
    while True:
        try:
            return parse(prompt())
        except Invalid as e:
            if not ask.interactive or ask.yes:
                sys.exit("error: %s" % e)
            print("  %s; try again" % e)

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
    def prompt():
        want = words(title)
        hint = [k for k, label in sorted(known.items()) if want & (words(k) | words(label))]
        print("\nTags (comma separated, Tab completes). Known: %s" % ", ".join(sorted(known)))
        complete_with(sorted(known))
        return ask.text("Tags", ", ".join(hint), required=False)

    def parse(raw):
        out = []
        for t in raw.split(","):
            t = slug(t)
            if t and t not in out:
                out.append(t)
        if len(out) > MAX_TAGS:
            raise Invalid("at most %d tags per page" % MAX_TAGS)
        return out

    tags = resolve(ask, args.tags, parse, prompt)
    new = {}
    for t in [t for t in tags if t not in known]:
        label = " ".join(w.capitalize() for w in t.split("-"))
        print("\"%s\" is a new tag (label \"%s\")." % (t, label))
        if ask.confirm("Add it to the tag list?", default=False):
            new[t] = label
        else:
            tags.remove(t)
    return tags, new


def split_list(raw):
    """Comma (or space) separated answer as a list, without blanks or repeats."""
    out = []
    for x in re.split(r"[,\s]+", raw):
        if x and x not in out:
            out.append(x)
    return out


def closest(word, allowed):
    """The allowed value a typo or short form most likely means ("hpc" -> systems-and-hpc), or ""."""
    word = slug(word)
    for a in allowed:
        if word in a.split("-"):
            return a
    near = difflib.get_close_matches(word, allowed, n=1, cutoff=0.7)
    return near[0] if near else ""


def choose_list(label, raw, allowed, limit):
    out = split_list(raw)
    bad = [x for x in out if x not in allowed]
    if bad:
        hints = ["%s (did you mean %s?)" % (x, closest(x, allowed)) if closest(x, allowed) else x for x in bad]
        raise Invalid("unknown %s %s; allowed: %s" % (label, ", ".join(hints), ", ".join(allowed)))
    if len(out) > limit:
        raise Invalid("at most %d %s per page" % (limit, label))
    return out


def choose_type(args, ask, folder, folders):
    """One or two kinds, the main one first. Returns a list."""
    types = load_section("types")

    def prompt():
        near = neighbours(folder, folders, "type")
        print("\nKind of page, one or two comma separated (the main one first): %s" % ", ".join(types))
        print("  concept explains an idea, guide shows how to do something, reference is for looking up,")
        print("  note is a short write-up, problem/project/experiment describe work")
        complete_with(types)
        return ask.text("Type", near[0] if near else "concept")

    return resolve(ask, args.type, lambda raw: choose_list("type", raw, types, MAX_TYPES), prompt)


def domain_words():
    """{domain: words of its key, label and description} from taxonomy.yaml."""
    out, current, inside = {}, None, False
    for line in read(TAXONOMY).splitlines():
        if re.match(r"^\S", line):
            inside = line.split("#")[0].rstrip() == "domains:"
            continue
        m = inside and re.match(r"^  ([a-z0-9-]+):", line)
        if m:
            current = m.group(1)
            out[current] = words(current.replace("-", " "))
        elif inside and current:
            out[current] |= words(line.split(":", 1)[-1])
    return out


def guess_domains(title, folder):
    """Domains whose description shares words with the title or folder path."""
    want = words(title) | words(folder.replace("/", " ").replace("-", " "))
    want -= {"field", "concept", "tool"}
    scored = sorted((-len(want & w), d) for d, w in domain_words().items() if want & w)
    return [d for n, d in scored if n == scored[0][0]]   # only the best match(es)


def choose_domains(args, ask, folder, folders, title):
    """One or two subjects. Returns (domains, new_domains); an unknown subject is matched to a
    known one ("hpc" -> systems-and-hpc) or, when typed in answer to the question, can be added."""
    domains = load_section("domains")
    new = {}

    def prompt():
        near = neighbours(folder, folders, "domains")
        if not near:
            near = next((v for k, v in sorted(folder_defaults().items(), key=lambda kv: -len(kv[0]))
                         if folder == k or folder.startswith(k + "/")), [])
        if not near:
            near = guess_domains(title, folder)
        print("\nSubjects (domains) put the page in Explore by subject; one or two, comma separated.")
        print("Known: %s" % ", ".join(domains + list(new)))
        complete_with(domains + list(new))
        return ask.text("Domains", ", ".join(near[:MAX_DOMAINS]), required=False)

    can_ask = args.domains is None and ask.interactive and not ask.yes

    def parse(raw):
        known = domains + list(new)
        out = []
        for x in split_list(raw):
            if x not in known and can_ask:
                guess = closest(x, known)
                key = slug(x)
                label = " ".join(w.capitalize() for w in key.split("-"))
                if guess and ask.confirm("Unknown subject \"%s\". Use %s?" % (x, guess)):
                    x = guess
                elif key and ask.confirm("Add \"%s\" (label \"%s\") as a new subject?" % (key, label), default=False):
                    description = ""
                    while not description:
                        description = ask.text("One line describing it")
                    new[key] = (label, description)
                    x = key
            if x not in out:
                out.append(x)
        return choose_list("domains", ", ".join(out), domains + list(new), MAX_DOMAINS)

    return resolve(ask, args.domains, parse, prompt), new


def reading_time(body):
    """Minutes at 200 words a minute, fenced code excluded, at least 1 (as on the site)."""
    return max(1, math.ceil(len(FENCE_BLOCK.sub(" ", body).split()) / WORDS_PER_MIN))


def check_page(rel):
    """Print the page's reading time and what is still missing. Returns the number of to-dos."""
    rel = rel.strip("/")
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        sys.exit("error: no page at %s" % rel)
    text = read(path)
    m = re.match(r"---\r?\n.*?\r?\n---\r?\n", text, re.S)
    body = text[m.end():] if m else text
    fm = front_matter(rel)
    minutes = reading_time(body)
    words_n = len(FENCE_BLOCK.sub(" ", body).split())
    print("%s\n  Reading time: %d min (%d words; the site shows this under the title)%s"
          % (rel, minutes, words_n, ", a quick read in Start here" if minutes <= QUICK_MIN else ""))
    todo = []
    outline = re.findall(r"<!--\s*(.*?)\s*-->", body, re.S)
    if outline:
        todo.append("%d outline note(s) from the template are still there (<!-- ... -->), e.g. \"%s\""
                    % (len(outline), outline[0][:60]))
    empty = [h for h, nxt in re.findall(r"^## (.+)\n+(?=(## |\Z))", body, re.M)]
    if empty:
        todo.append("empty section(s): %s; fill or remove them" % ", ".join(empty))
    if not m:
        todo.append("no front matter; create pages with this script, or copy the block from CLAUDE.md section 21")
    for key, why in (("summary", "one line shown in search and Explore"),
                     ("type", "concept, guide, reference, ..."),
                     ("domains", "puts the page in Explore by subject"),
                     ("tags", "up to 5 from taxonomy.yaml"),
                     ("level", "beginner pages show under Beginner friendly")):
        if m and not fm.get(key):
            todo.append("no %s (%s)" % (key, why))
    if len(fm.get("summary", "")) > 200:
        todo.append("summary is over 200 characters")
    plain = FENCE_BLOCK.sub(" ", body)
    unnamed = len(re.findall(r"!\[(?:image|img|)\]\(", plain, re.I))
    if unnamed:
        todo.append("%d picture(s) without a description: write what each shows in ![...]" % unnamed)
    rel_links = re.findall(r"(?<!!)\[[^\]]*\]\((\.{1,2}/[^)]*)\)", plain)
    if rel_links:
        todo.append("relative link(s) break on the site, write them root-absolute: %s" % ", ".join(rel_links[:3]))
    if not re.search(r"^# ", body, re.M):
        todo.append("no # title heading")
    if todo:
        print("  To do:")
        for t in todo:
            print("  - " + t)
    else:
        print("  Nothing missing.")
    print("  Before pushing: python3 .docs/tools/validate.py && python3 .docs/tools/check_links.py")
    return len(todo)


def yaml_value(v):
    if re.search(r"[:#\[\]{},&*!|>'\"%@`]|^\s|\s$|^[-?]", v):
        return '"%s"' % v.replace("\\", "\\\\").replace('"', '\\"')
    return v


def link_in_readme(folder, page_rel, title, summary):
    """Add the page to the folder README's index: a File/Directory table, or
    failing that the last bullet list of links. Returns a message."""
    readme = os.path.join(ROOT, folder, "README.md")
    stem = os.path.basename(page_rel)[:-3]
    row = "| [%s](/%s) | %s |" % (stem, page_rel, summary or title)
    bullet = "- [%s](/%s)" % (title, page_rel)
    if not os.path.exists(readme):
        return "No README.md in %s; the sidebar still lists the page." % folder
    lines = read(readme).splitlines(keepends=True)
    for i, line in enumerate(lines):
        if TABLE_HEAD.match(line):
            start = end = i + 2
            while end < len(lines) and lines[end].startswith("|"):
                end += 1
            if not lines[end - 1].endswith("\n"):
                lines[end - 1] += "\n"
            # Keep the table's order when it is alphabetical; otherwise append.
            keys = [re.sub(r"^\|\s*\[([^\]]*)\].*", r"\1", l).lower() for l in lines[start:end]]
            pos = end
            if keys == sorted(keys):
                pos = start + sum(1 for k in keys if k < stem)
            lines.insert(pos, row + "\n")
            break
    else:
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


def page_ids(raw, ids, role):
    out = split_list(raw)
    unknown = [r for r in out if r not in ids]
    if unknown:
        hints = ["%s (did you mean %s?)" % (r, closest(r, sorted(ids))) if closest(r, sorted(ids)) else r
                 for r in unknown]
        raise Invalid("no page has the id %s; only pages with an id in their front matter can be %s"
                      % (", ".join(hints), role))
    return out


def main():
    p = argparse.ArgumentParser(description="Create a new page with front matter, an index link and a fresh sidebar.")
    p.add_argument("--title")
    p.add_argument("--summary", help="one line, shown in search results")
    p.add_argument("--folder", help="e.g. fields/deep-learning/concepts")
    p.add_argument("--name", help="file name without .md (default: from the title)")
    p.add_argument("--tags", help="comma separated, e.g. transformers,attention")
    p.add_argument("--level", choices=LEVELS, help="beginner pages show under 'Beginner friendly'")
    p.add_argument("--type", help="one or two of concept, guide, reference, note, problem, project, experiment, comma separated")
    p.add_argument("--domains", help="one or two comma separated subjects from taxonomy.yaml, e.g. deep-learning")
    p.add_argument("--prerequisites", help="comma separated page ids to read first, e.g. deep-learning-basics")
    p.add_argument("--related", help="comma separated page ids to see also")
    p.add_argument("--check", metavar="PAGE", help="report a written page's reading time and what is missing")
    p.add_argument("--yes", action="store_true", help="accept defaults and suggestions without asking")
    p.add_argument("--dry-run", action="store_true", help="show what would be written, change nothing")
    args = p.parse_args()
    if args.check:
        return 1 if check_page(args.check) else 0
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

    page_types = choose_type(args, ask, folder, folders)
    domains, new_domains = choose_domains(args, ask, folder, folders, title)
    tags, new_tags = choose_tags(args, ask, title, load_tags())

    def parse_level(raw):
        raw = raw.strip().lower()
        if raw and raw not in LEVELS:
            raise Invalid("level must be one of %s" % ", ".join(LEVELS))
        return raw
    level = resolve(ask, args.level, parse_level,
                    lambda: ask.text("Level (%s, optional)" % "/".join(LEVELS), required=False))
    ids = existing_ids(folders)

    def ask_ids(heading, label):
        def prompt():
            print("\n%s: ids of pages to %s (comma separated, Tab completes)." % (heading, label))
            complete_with(sorted(ids))
            return ask.text(heading, required=False)
        return prompt
    prereqs = resolve(ask, args.prerequisites, lambda raw: page_ids(raw, ids, "a prerequisite"),
                      ask_ids("Prerequisites", "read first"))
    related = [r for r in resolve(ask, args.related, lambda raw: page_ids(raw, ids, "related"),
                                  ask_ids("Related", "see also")) if r not in prereqs]

    page_id = name if name not in ids else slug(folder.split("/")[-1] + "-" + name)
    fm = ["---", "id: %s" % page_id, "title: %s" % yaml_value(title)]
    label = sidebar_label(title)
    if label != title:
        print("\nNote: the sidebar shows the text after the last hyphen (\"%s\")." % label)
        print("      sidebar_label is set, so the sidebar shows the full title.")
        fm.append("sidebar_label: %s" % yaml_value(title))
    if summary:
        fm.append("summary: %s" % yaml_value(summary))
    if level:
        fm.append("level: %s" % level)
    if page_types:
        fm.append("type: %s" % (page_types[0] if len(page_types) == 1 else "[%s]" % ", ".join(page_types)))
    if domains:
        fm.append("domains: [%s]" % ", ".join(domains))
    if tags:
        fm.append("tags: [%s]" % ", ".join(tags))
    if prereqs or related:
        fm.append("relations:")
        if prereqs:
            fm.append("  prerequisites: [%s]" % ", ".join(prereqs))
        if related:
            fm.append("  related: [%s]" % ", ".join(related))
    fm.append("---")
    intro = summary or "<!-- One or two sentences: what will the reader learn? -->"
    content = "\n".join(fm) + "\n\n" + BODY.format(title=title, intro=intro)

    if args.dry_run:
        print("\n--- %s ---\n%s" % (page_rel, content))
        if new_tags:
            print("New tags for taxonomy.yaml: %s" % ", ".join(new_tags))
        if new_domains:
            print("New subjects for taxonomy.yaml: %s" % ", ".join(new_domains))
        return

    full = os.path.join(ROOT, page_rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print("\nCreated  %s" % page_rel)
    if new_tags:
        add_tags(new_tags)
        print("Added    tags %s to .docs/metadata/taxonomy.yaml" % ", ".join(sorted(new_tags)))
    if new_domains:
        add_domains(new_domains)
        print("Added    subjects %s to .docs/metadata/taxonomy.yaml" % ", ".join(new_domains))
    print(link_in_readme(folder, page_rel, title, summary))

    docs = os.path.join(ROOT, ".docs")
    for script in ("gen_sidebar.sh", "gen_navbar.sh"):
        subprocess.run(["bash", script], cwd=docs, check=True, stdout=subprocess.DEVNULL)
    print("Updated  .docs/_sidebar.md and .docs/_navbar.md")
    print("\nNext: write the page. The site shows its reading time from the text; to see it")
    print("and what is still missing, run:  python3 .docs/tools/new_page.py --check %s" % page_rel)
    print("Then commit it on a branch from dev.")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nStopped: nothing more was changed.")
