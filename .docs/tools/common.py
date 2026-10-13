"""Shared helpers for the metadata tools (validate, generate_index, stage_site)."""
import os
import re
import subprocess

import yaml

ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RELATION_KEYS = ("related", "prerequisites")

# '---' on the first line, optional body, closing '---' on its own line (LF or CRLF).
FRONT_MATTER_RE = re.compile(
    r"\A﻿?---[ \t]*\r?\n(?:(?P<yaml>.*?)\r?\n)?---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
OPENS_RE = re.compile(r"\A﻿?---[ \t]*\r?\n")


class DupKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys."""


def _construct_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark)
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


DupKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def split_front_matter(text):
    """Return (yaml_text, body_offset), or None when the page has no front matter.

    Raises ValueError if the page opens with '---' but the block is never closed.
    """
    m = FRONT_MATTER_RE.match(text)
    if m:
        return m.group("yaml") or "", m.end()
    if OPENS_RE.match(text):
        raise ValueError("front matter opened with '---' on line 1 but never closed")
    return None


def submodule_paths(root):
    gm = os.path.join(root, ".gitmodules")
    if not os.path.exists(gm):
        return []
    out = subprocess.run(
        ["git", "config", "-f", gm, "--get-regexp", r"\.path$"],
        capture_output=True, text=True).stdout
    return sorted(line.split(None, 1)[1].strip() for line in out.splitlines() if line.strip())


def list_pages(root, submodules):
    """Sorted repo-relative .md paths; skips dot dirs, node_modules and submodules."""
    pages = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
        dirnames[:] = sorted(
            d for d in dirnames
            if not d.startswith(".")
            and d not in ("node_modules", "_site")
            and (d if rel_dir == "." else f"{rel_dir}/{d}") not in submodules)
        for name in sorted(filenames):
            if name.endswith(".md"):
                pages.append(name if rel_dir == "." else f"{rel_dir}/{name}")
    return pages


def fallback_id(path):
    p = path[:-3]
    if p == "README":
        return "readme"
    if p.endswith("/README"):
        p = p[: -len("/README")]
    return p.replace("/", "-").lower()


def read_text(root, path):
    with open(os.path.join(root, path), encoding="utf-8", errors="replace", newline="") as f:
        return f.read()


def load_taxonomy_full(root):
    with open(os.path.join(root, ".docs/metadata/taxonomy.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)
