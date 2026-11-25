"""Page scaffolding data: paths, the taxonomy, front matter and the page check.

Part of new_page.py (split for size): no questions are asked here, and nothing here
writes to the index. Tests that move the repository root set `page_scaffold.ROOT`.
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


MAX_DOMAINS = 3          # a convention, not a technical limit: validate.py only warns above it


MAX_TYPES = 2


LEVELS = ("beginner", "intermediate", "advanced")


FM_ORDER = ("id", "title", "sidebar_label", "sidebar_group", "order", "summary", "level", "type", "status",
            "domains", "tags", "relations")


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


def add_types(new):
    """Add new page kinds ({key: description}) at the end of the types block."""
    lines = read(TAXONOMY).splitlines(keepends=True)
    start = next(i for i, l in enumerate(lines) if l.split("#")[0].rstrip() == "types:")
    end = start + 1
    while end < len(lines) and not re.match(r"^\S", lines[end]):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    lines[end:end] = ["  %s: %s\n" % (key, description) for key, description in new.items()]
    with open(TAXONOMY, "w", encoding="utf-8") as f:
        f.writelines(lines)


def add_domains(new, chosen=()):
    """Append new domains ({key: (label, description)}) to the end of the domains block, each related
    to the other subjects `chosen` for the page it was created for."""
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
        others = [d for d in chosen if d != key]
        if others:
            add.append("    related: [%s]\n" % ", ".join(others))
    lines[end:end] = add
    with open(TAXONOMY, "w", encoding="utf-8") as f:
        f.writelines(lines)


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
        elif inside and current and not line.strip().startswith("related:"):
            out[current] |= words(line.split(":", 1)[-1])
    return out


def related_map():
    """{domain: set of related domains} from taxonomy.yaml, read both ways (a pair is listed once)."""
    out, current, inside = {}, None, False
    for line in read(TAXONOMY).splitlines():
        if re.match(r"^\S", line):
            inside = line.split("#")[0].rstrip() == "domains:"
            continue
        m = inside and re.match(r"^  ([a-z0-9-]+):\s*$", line)
        if m:
            current = m.group(1)
            out.setdefault(current, set())
            continue
        m = inside and current and re.match(r"^    related:\s*\[(.*)\]", line)
        if m:
            for other in [x.strip() for x in m.group(1).split(",") if x.strip()]:
                out[current].add(other)
                out.setdefault(other, set()).add(current)
    return out


def unrelated_pairs(domains, fresh=()):
    """Pairs among `domains` not marked as related in taxonomy.yaml. A domain being created in this
    run (`fresh`) is made related to the others, so it never counts."""
    rel = related_map()
    return [(a, b) for i, a in enumerate(domains) for b in domains[i + 1:]
            if a not in fresh and b not in fresh and b not in rel.get(a, set())]


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


SEPARATOR = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def front_matter_lines(page_id, title, summary, meta, note=True):
    """The front matter block as a list of lines, from "---" to "---"."""
    fm = ["---", "id: %s" % page_id, "title: %s" % yaml_value(title)]
    label = sidebar_label(title)
    if label != title:
        if note:
            print("\nNote: the sidebar shows the text after the last hyphen (\"%s\")." % label)
            print("      sidebar_label is set, so the sidebar shows the full title.")
        fm.append("sidebar_label: %s" % yaml_value(title))
    if summary:
        fm.append("summary: %s" % yaml_value(summary))
    if meta["level"]:
        fm.append("level: %s" % meta["level"])
    if meta["types"]:
        fm.append("type: %s" % (meta["types"][0] if len(meta["types"]) == 1 else "[%s]" % ", ".join(meta["types"])))
    if meta["domains"]:
        fm.append("domains: [%s]" % ", ".join(meta["domains"]))
    if meta["tags"]:
        fm.append("tags: [%s]" % ", ".join(meta["tags"]))
    if meta["prereqs"] or meta["related"]:
        fm.append("relations:")
        if meta["prereqs"]:
            fm.append("  prerequisites: [%s]" % ", ".join(meta["prereqs"]))
        if meta["related"]:
            fm.append("  related: [%s]" % ", ".join(meta["related"]))
    fm.append("---")
    return fm


def key_blocks(lines):
    """{key: [lines]} of a front matter block: each top-level key with its indented lines."""
    blocks, current = {}, None
    for line in lines:
        if line.strip() == "---":
            continue
        m = re.match(r"^([A-Za-z_]+):", line)
        if m:
            current = m.group(1)
            blocks[current] = []
        if current:
            blocks[current].append(line)
    return blocks


def merge_front_matter(existing, added, skip=()):
    """Existing front matter lines plus the added fields the page lacks, in the usual order.
    What is already there is kept exactly as written; `skip` names fields not to add."""
    have, new = key_blocks(existing), key_blocks(added)
    new = {k: v for k, v in new.items() if k not in skip}
    order = [k for k in FM_ORDER if k in have or k in new] + [k for k in have if k not in FM_ORDER]
    return ["---"] + [l for k in order for l in (have[k] if k in have else new[k])] + ["---"]


def report_new(meta):
    if meta["new_tags"]:
        print("New tags for taxonomy.yaml: %s" % ", ".join(meta["new_tags"]))
    if meta["new_domains"]:
        print("New subjects for taxonomy.yaml: %s" % ", ".join(meta["new_domains"]))
    if meta.get("new_types"):
        print("New kinds for taxonomy.yaml: %s" % ", ".join(meta["new_types"]))


def save_taxonomy(meta):
    if meta["new_tags"]:
        add_tags(meta["new_tags"])
        print("Added    tags %s to .docs/metadata/taxonomy.yaml" % ", ".join(sorted(meta["new_tags"])))
    if meta["new_domains"]:
        add_domains(meta["new_domains"], meta["domains"])
        print("Added    subjects %s to .docs/metadata/taxonomy.yaml" % ", ".join(meta["new_domains"]))
    if meta.get("new_types"):
        add_types(meta["new_types"])
        print("Added    kinds %s to .docs/metadata/taxonomy.yaml" % ", ".join(meta["new_types"]))


def body_h1(text):
    """The first "# " heading outside code fences."""
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and line.startswith("# "):
            return line[2:].strip()
    return ""


def key_value(text):
    key, _, value = text.partition("=")
    key = slug(key)
    if not key:
        raise argparse.ArgumentTypeError("expected KEY=VALUE")
    return key, value.strip()


def parse_front(lines):
    """{key: value} of front matter lines: scalars as text, one-line [a, b] lists and - item lists as lists,
    and the relations block as prerequisites / related lists."""
    out = {}
    for key, block in key_blocks(lines).items():
        head = block[0].split(":", 1)[1].strip()
        if key == "relations":
            for line in block[1:]:
                m = re.match(r"^\s+(prerequisites|related):\s*\[(.*)\]\s*$", line)
                if m:
                    out[m.group(1)] = [x.strip() for x in m.group(2).split(",") if x.strip()]
        elif head.startswith("["):
            out[key] = [x.strip().strip("\"'") for x in head[1:head.rfind("]")].split(",") if x.strip()]
        elif head:
            out[key] = head.strip("\"'")
        else:
            out[key] = [re.sub(r"^\s+-\s*", "", l).strip().strip("\"'") for l in block[1:] if re.match(r"^\s+-", l)]
    return out


UPDATE_KEYS = {"summary": ("summary",), "level": ("level",), "types": ("type",), "domains": ("domains",),
               "tags": ("tags",), "relations": ("relations",)}
