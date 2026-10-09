#!/usr/bin/env python3
"""Validate front matter against .docs/metadata/{schema,taxonomy}.yaml.

Pages without front matter are legacy and allowed. Git submodule paths
(from .gitmodules) are skipped entirely. Exits 1 on any error.

Usage: python3 .docs/tools/validate.py [--root PATH]
"""
import argparse
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DupKeyLoader, ID_RE, RELATION_KEYS, fallback_id, list_pages,  # noqa: E402
                    read_text, split_front_matter, submodule_paths)

ALLOWED_KEYS = {"id", "title", "type", "status", "domains", "tags", "relations"}
REQUIRED_KEYS = ("title", "type", "status", "domains")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, path, line, msg):
        self.errors.append((path, line, msg))

    def warn(self, path, line, msg):
        self.warnings.append((path, line, msg))

    def emit(self):
        gha = os.environ.get("GITHUB_ACTIONS") == "true"
        for level, items in (("error", self.errors), ("warning", self.warnings)):
            for path, line, msg in sorted(items):
                print(f"{path}:{line}: {level}: {msg}")
                if gha:
                    print(f"::{level} file={path},line={line}::{msg}")


def key_lines(yaml_text):
    """Map top-level key -> line, plus (key, index) / (key, sub, index) -> line (file lines)."""
    lines = {}
    try:
        node = yaml.compose(yaml_text, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        return lines
    if not isinstance(node, yaml.MappingNode):
        return lines

    def walk(mapping, prefix):
        for k, v in mapping.value:
            key = prefix + (k.value,)
            lines[key] = k.start_mark.line + 2  # +1 for 1-based, +1 for the opening '---'
            if isinstance(v, yaml.SequenceNode):
                for idx, item in enumerate(v.value):
                    lines[key + (idx,)] = item.start_mark.line + 2
            elif isinstance(v, yaml.MappingNode) and not prefix:
                walk(v, key)

    walk(node, ())
    return lines


def load_taxonomy(root, rep):
    path = ".docs/metadata/taxonomy.yaml"
    try:
        with open(os.path.join(root, path), encoding="utf-8") as f:
            tax = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        rep.error(path, 1, f"cannot load taxonomy: {e}")
        return None
    for section in ("types", "statuses", "relation_types", "domains", "tags"):
        if section not in tax:
            rep.error(path, 1, f"missing section '{section}'")
            return None
    for section in ("domains", "tags"):
        for k in tax[section]:
            if not ID_RE.match(str(k)):
                rep.error(path, 1, f"{section} key {k!r} is not kebab-case")
    if sorted(tax["relation_types"]) != sorted(RELATION_KEYS):
        rep.error(path, 1, f"relation_types must be exactly {list(RELATION_KEYS)}")
    return {
        "types": set(tax["types"]),
        "statuses": set(tax["statuses"]),
        "domains": set(tax["domains"]),
        "tags": set(tax["tags"]),
    }


def check_enum_list(rep, path, lines, key, value, allowed, required):
    kl = lines.get((key,), 1)
    if not isinstance(value, list):
        rep.error(path, kl, f"'{key}' must be a list")
        return
    if required and not value:
        rep.error(path, kl, f"'{key}' must contain at least one value")
    seen = set()
    for i, v in enumerate(value):
        ln = lines.get((key, i), kl)
        if not isinstance(v, str) or v not in allowed:
            rep.error(path, ln, f"invalid {key[:-1] if key.endswith('s') else key} {v!r}; "
                                f"not in taxonomy ({', '.join(sorted(allowed))})")
        elif v in seen:
            rep.error(path, ln, f"duplicate value {v!r} in '{key}'")
        seen.add(v)


def validate_page(path, text, tax, rep):
    """Return dict(id, relations, has_fm) for pages with valid-enough front matter, else None."""
    try:
        split = split_front_matter(text)
    except ValueError as e:
        rep.error(path, 1, str(e))
        return None
    if split is None:
        return None
    yaml_text, _ = split

    for n, raw in enumerate(yaml_text.splitlines(), start=2):
        if raw.lstrip().startswith("#"):
            rep.error(path, n, "YAML comments are not allowed in front matter "
                               "(gen_sidebar.sh would read them as the page title)")

    try:
        data = yaml.load(yaml_text, Loader=DupKeyLoader)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        rep.error(path, (mark.line + 2) if mark else 1, f"invalid YAML: {getattr(e, 'problem', e)}")
        return None
    if not isinstance(data, dict):
        rep.error(path, 1, "front matter must be a YAML mapping")
        return None

    lines = key_lines(yaml_text)
    for k in data:
        if k not in ALLOWED_KEYS:
            rep.error(path, lines.get((k,), 1), f"unknown key {k!r}")
    for k in REQUIRED_KEYS:
        if k not in data:
            rep.error(path, 1, f"missing required field '{k}'")

    page_id = data.get("id")
    if "id" in data:
        if not isinstance(page_id, str) or not ID_RE.match(page_id):
            rep.error(path, lines.get(("id",), 1),
                      f"id {page_id!r} must be kebab-case (lowercase letters, digits, '-')")
            page_id = None
    if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip()):
        rep.error(path, lines.get(("title",), 1), "title must be a non-empty string")
    if "type" in data and data["type"] not in tax["types"]:
        rep.error(path, lines.get(("type",), 1),
                  f"invalid type {data['type']!r}; allowed: {', '.join(sorted(tax['types']))}")
    if "status" in data and data["status"] not in tax["statuses"]:
        rep.error(path, lines.get(("status",), 1),
                  f"invalid status {data['status']!r}; allowed: {', '.join(sorted(tax['statuses']))}")
    if "domains" in data:
        check_enum_list(rep, path, lines, "domains", data["domains"], tax["domains"], True)
    if "tags" in data:
        check_enum_list(rep, path, lines, "tags", data["tags"], tax["tags"], False)

    relations = {}
    rel = data.get("relations")
    if "relations" in data:
        if not isinstance(rel, dict):
            rep.error(path, lines.get(("relations",), 1), "'relations' must be a mapping")
        else:
            for rk, rv in rel.items():
                rl = lines.get(("relations", rk), lines.get(("relations",), 1))
                if rk not in RELATION_KEYS:
                    rep.error(path, rl, f"unknown relation type {rk!r}; allowed: {', '.join(RELATION_KEYS)}")
                elif not isinstance(rv, list) or not all(isinstance(x, str) for x in rv):
                    rep.error(path, rl, f"relations.{rk} must be a list of ids")
                else:
                    relations[rk] = [(x, lines.get(("relations", rk, i), rl)) for i, x in enumerate(rv)]
        if any(relations.values()) and "id" not in data:
            rep.error(path, lines.get(("relations",), 1),
                      "pages that declare relations need an explicit 'id'")
    return {"id": page_id, "relations": relations}


def run(root):
    rep = Report()
    root = os.path.abspath(root)
    tax = load_taxonomy(root, rep)
    if tax is None:
        return rep, 0, 0

    subs = submodule_paths(root)
    pages = list_pages(root, set(subs))

    fm_pages = {}    # path -> info
    fallbacks = {}   # fallback id -> [paths]
    for path in pages:
        fallbacks.setdefault(fallback_id(path), []).append(path)
        text = read_text(root, path)
        info = validate_page(path, text, tax, rep)
        if info is not None:
            fm_pages[path] = info

    # id uniqueness: explicit vs explicit, explicit vs any page's fallback
    explicit = {}
    for path in sorted(fm_pages):
        pid = fm_pages[path]["id"]
        if pid:
            explicit.setdefault(pid, []).append(path)
    for pid, paths in sorted(explicit.items()):
        if len(paths) > 1:
            for p in paths:
                rep.error(p, 1, f"duplicate id {pid!r} (also in {', '.join(x for x in paths if x != p)})")
        for other in fallbacks.get(pid, []):
            if other not in paths:
                for p in paths:
                    rep.error(p, 1, f"id {pid!r} collides with the path-derived fallback id of {other}")
    for fid, paths in sorted(fallbacks.items()):
        if len(paths) > 1:
            rep.warn(paths[0], 1, f"legacy fallback ids collide: {fid!r} for {', '.join(paths)}")

    # relation targets
    for path in sorted(fm_pages):
        for rk, items in sorted(fm_pages[path]["relations"].items()):
            for target, ln in items:
                if target == fm_pages[path]["id"]:
                    rep.error(path, ln, f"relations.{rk}: page cannot relate to itself")
                elif target not in explicit:
                    if any(target == s or target.startswith(s + "/") for s in subs):
                        rep.error(path, ln, f"relations.{rk}: {target!r} points into a git submodule; "
                                            "relations may not target submodule content")
                    elif target in fallbacks:
                        rep.error(path, ln, f"relations.{rk}: {target!r} is only a path-derived fallback id; "
                                            "give the target page an explicit 'id'")
                    else:
                        rep.error(path, ln, f"relations.{rk}: unknown id {target!r}")
    return rep, len(pages), len(fm_pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    args = ap.parse_args()
    rep, n_pages, n_fm = run(args.root)
    rep.emit()
    print(f"checked {n_pages} pages ({n_fm} with front matter): "
          f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()
