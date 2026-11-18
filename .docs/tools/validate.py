#!/usr/bin/env python3
"""Validate front matter against .docs/metadata/{schema,taxonomy}.yaml.

Pages without front matter are legacy and allowed. Git submodule paths
(from .gitmodules) are skipped entirely. Exits 1 on any error.

Usage: python3 .docs/tools/validate.py [--root PATH]
"""
import argparse
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DupKeyLoader, ID_RE, RELATION_KEYS, fallback_id, list_pages,  # noqa: E402
                    read_text, split_front_matter, submodule_paths)

ALLOWED_KEYS = {"id", "title", "sidebar_label", "sidebar_group", "order", "summary", "level", "type", "status", "domains", "tags", "relations"}
SUMMARY_MAX = 200
LABEL_WARN = 40
MAX_TAGS = 5
MAX_TYPES = 2
MAX_DOMAINS = 3          # more than this is only a warning


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.summary_missing = []   # content pages without a summary (optional, recommended)
        self.summary_total = 0      # content pages: every page except folder indexes

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
    related = {}
    for d, meta in tax["domains"].items():
        for other in (meta.get("related") or []) if isinstance(meta, dict) else []:
            if other not in tax["domains"]:
                rep.error(path, 1, f"domain {d!r} lists unknown related domain {other!r}")
            elif other != d:
                related.setdefault(d, set()).add(other)
                related.setdefault(other, set()).add(d)        # a pair is listed once and read both ways
    if sorted(tax["relation_types"]) != sorted(RELATION_KEYS):
        rep.error(path, 1, f"relation_types must be exactly {list(RELATION_KEYS)}")
    return {
        "types": set(tax["types"]),
        "tags_all": set(tax["tags"]),
        "tech_tags": {t for t, m in tax["tags"].items() if isinstance(m, dict) and m.get("kind") == "technology"},
        "statuses": set(tax["statuses"]),
        "levels": set(tax.get("levels") or []),
        "domains": set(tax["domains"]),
        "domain_related": related,
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

    page_id = data.get("id")
    if "id" in data:
        if not isinstance(page_id, str) or not ID_RE.match(page_id):
            rep.error(path, lines.get(("id",), 1),
                      f"id {page_id!r} must be kebab-case (lowercase letters, digits, '-')")
            page_id = None
    if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip()):
        rep.error(path, lines.get(("title",), 1), "title must be a non-empty string")
    label = None
    if "sidebar_label" in data:
        sl = data["sidebar_label"]
        if not isinstance(sl, str) or not sl.strip() or "\n" in sl.strip():
            rep.error(path, lines.get(("sidebar_label",), 1), "sidebar_label must be one non-empty line")
        else:
            label = sl.strip()
            if len(label) > LABEL_WARN:
                rep.warn(path, lines.get(("sidebar_label",), 1),
                         f"sidebar_label is {len(label)} characters; keep it under {LABEL_WARN} so it fits the sidebar")
    group = None
    if "sidebar_group" in data:
        sg = data["sidebar_group"]
        gl = lines.get(("sidebar_group",), 1)
        if os.path.basename(path) != "README.md":
            rep.error(path, gl, "sidebar_group only applies to a folder's README.md")
        elif not isinstance(sg, str) or not sg.strip() or "\n" in sg.strip():
            rep.error(path, gl, "sidebar_group must be one non-empty line")
        else:
            group = sg.strip()
            if len(group) > LABEL_WARN:
                rep.warn(path, gl, f"sidebar_group is {len(group)} characters; keep it under {LABEL_WARN}")
    order = None
    if "order" in data:
        ov = data["order"]
        if isinstance(ov, bool) or not isinstance(ov, int) or ov < 1:
            rep.error(path, lines.get(("order",), 1), "order must be a whole number from 1 up")
        else:
            order = ov
    if "summary" in data:
        sm = data["summary"]
        if not isinstance(sm, str) or not sm.strip():
            rep.error(path, lines.get(("summary",), 1), "summary must be a non-empty string")
        elif "\n" in sm.strip() or len(sm) > SUMMARY_MAX:
            rep.error(path, lines.get(("summary",), 1),
                      f"summary must be one line of at most {SUMMARY_MAX} characters")
    if "level" in data and data["level"] not in tax["levels"]:
        rep.error(path, lines.get(("level",), 1),
                  f"invalid level {data['level']!r}; allowed: {', '.join(sorted(tax['levels']))}")
    if "type" in data:
        tv = data["type"]
        if isinstance(tv, list):
            check_enum_list(rep, path, lines, "type", tv, tax["types"], True)
            if len(tv) > MAX_TYPES:
                rep.error(path, lines.get(("type",), 1), f"at most {MAX_TYPES} types per page ({len(tv)} given)")
        elif not isinstance(tv, str) or tv not in tax["types"]:
            rep.error(path, lines.get(("type",), 1),
                      f"invalid type {tv!r}; allowed: {', '.join(sorted(tax['types']))}")
    if "status" in data and data["status"] not in tax["statuses"]:
        rep.error(path, lines.get(("status",), 1),
                  f"invalid status {data['status']!r}; allowed: {', '.join(sorted(tax['statuses']))}")
    if "domains" in data:
        check_enum_list(rep, path, lines, "domains", data["domains"], tax["domains"], True)
        doms = [d for d in data["domains"] if d in tax["domains"]] if isinstance(data["domains"], list) else []
        dl = lines.get(("domains",), 1)
        if len(doms) > MAX_DOMAINS:
            rep.warn(path, dl, f"{len(doms)} domains; pages are easier to find with at most {MAX_DOMAINS}")
        for i, a in enumerate(doms):
            for b in doms[i + 1:]:
                if b not in tax["domain_related"].get(a, set()):
                    rep.warn(path, dl, f"domains {a!r} and {b!r} are not marked as related in taxonomy.yaml; "
                                       "if the page really covers both, add one to the other's `related` list there")
    if "tags" in data:
        check_enum_list(rep, path, lines, "tags", data["tags"], tax["tags"], False)
        if isinstance(data["tags"], list) and len(data["tags"]) > MAX_TAGS:
            rep.error(path, lines.get(("tags",), 1), f"at most {MAX_TAGS} tags per page ({len(data['tags'])} given)")

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
    tags = data.get("tags") if isinstance(data.get("tags"), list) else []
    sm = data.get("summary")
    return {"has_summary": isinstance(sm, str) and bool(sm.strip()), "id": page_id, "relations": relations, "label": label, "group": group,
            "order": order, "order_line": lines.get(("order",), 1),
            "group_line": lines.get(("sidebar_group",), 1), "label_line": lines.get(("sidebar_label",), 1),
            "tags": [t for t in tags if isinstance(t, str)], "tags_line": lines.get(("tags",), 1)}


def is_folder_index(path, text):
    """A folder README with a `## Contents` list: navigation, not a page that needs a summary."""
    return os.path.basename(path) == "README.md" and re.search(r"^## Contents\s*$", text, re.M) is not None


def coverage_line(rep):
    """One line on how many content pages carry a summary. Never an error: a summary is optional."""
    have = rep.summary_total - len(rep.summary_missing)
    pct = round(100 * have / rep.summary_total) if rep.summary_total else 100
    return (f"summary coverage: {have} of {rep.summary_total} content pages ({pct}%); "
            "a summary is optional but recommended (list the rest with --list-missing-summaries)")


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
        if not is_folder_index(path, text):
            rep.summary_total += 1
            if info is None or not info["has_summary"]:
                rep.summary_missing.append(path)

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

    # sidebar labels must be unique within a folder
    labels = {}
    for path in sorted(fm_pages):
        lbl = fm_pages[path]["label"]
        if lbl:
            labels.setdefault((os.path.dirname(path), lbl.lower()), []).append(path)
    for (folder, _), paths in sorted(labels.items()):
        if len(paths) > 1:
            for p in paths:
                rep.error(p, fm_pages[p]["label_line"],
                          f"duplicate sidebar_label {fm_pages[p]['label']!r} in {folder or '.'} "
                          f"(also in {', '.join(x for x in paths if x != p)})")

    # order is the reading position inside a folder: unique per folder, and a
    # prerequisite in the same folder must come before the page that needs it
    orders = {}
    for path in sorted(fm_pages):
        if fm_pages[path]["order"]:
            orders.setdefault((os.path.dirname(path), fm_pages[path]["order"]), []).append(path)
    for (folder, num), paths in sorted(orders.items()):
        if len(paths) > 1:
            for p in paths:
                rep.error(p, fm_pages[p]["order_line"],
                          f"duplicate order {num} in {folder or '.'} "
                          f"(also in {', '.join(x for x in paths if x != p)})")
    by_id = {fm_pages[p]["id"]: p for p in fm_pages if fm_pages[p]["id"]}
    for path in sorted(fm_pages):
        mine = fm_pages[path]["order"]
        if not mine:
            continue
        for target, _ in fm_pages[path]["relations"].get("prerequisites", []):
            other = by_id.get(target)
            if other and os.path.dirname(other) == os.path.dirname(path):
                theirs = fm_pages[other]["order"]
                if theirs and theirs >= mine:
                    rep.warn(path, fm_pages[path]["order_line"],
                             f"order {mine} comes before its prerequisite {target!r} (order {theirs}); "
                             "readers are sent to the prerequisite first")

    groups = {}
    for path in sorted(fm_pages):
        grp = fm_pages[path]["group"]
        if grp:
            groups.setdefault((os.path.dirname(os.path.dirname(path)), grp.lower()), []).append(path)
    for (parent, _), paths in sorted(groups.items()):
        if len(paths) > 1:
            for p in paths:
                rep.error(p, fm_pages[p]["group_line"],
                          f"duplicate sidebar_group {fm_pages[p]['group']!r} in {parent or '.'} "
                          f"(also in {', '.join(x for x in paths if x != p)})")
    # tag rule: single-use tags must name a concrete technology (warning only)
    tag_use = {}
    for path in sorted(fm_pages):
        for t in set(fm_pages[path]["tags"]):
            tag_use.setdefault(t, []).append(path)
    for t, paths in sorted(tag_use.items()):
        if len(paths) == 1 and t in tax["tags_all"] and t not in tax["tech_tags"]:
            rep.warn(paths[0], fm_pages[paths[0]]["tags_line"],
                     f"tag {t!r} is used by only one page and is not marked kind: technology")

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
    # prerequisites must not form a cycle
    graph = {}
    where = {}
    for path in sorted(fm_pages):
        info = fm_pages[path]
        if info["id"]:
            where[info["id"]] = path
            graph[info["id"]] = [t for t, _ in info["relations"].get("prerequisites", []) if t in explicit]
    state = {}

    def visit(node, stack):
        state[node] = 1
        for nxt in sorted(graph.get(node, [])):
            if state.get(nxt) == 1:
                cycle = stack[stack.index(nxt):] + [nxt] if nxt in stack else [node, nxt]
                rep.error(where[node], 1, "prerequisites form a cycle: " + " -> ".join(cycle))
            elif state.get(nxt) is None:
                visit(nxt, stack + [nxt])
        state[node] = 2

    for node in sorted(graph):
        if state.get(node) is None:
            visit(node, [node])
    return rep, len(pages), len(fm_pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    ap.add_argument("--summary-coverage", action="store_true",
                    help="print only the summary coverage line (never fails on missing summaries)")
    ap.add_argument("--list-missing-summaries", action="store_true",
                    help="also list the content pages that have no summary")
    args = ap.parse_args()
    rep, n_pages, n_fm = run(args.root)
    if args.summary_coverage:
        print(coverage_line(rep))
        sys.exit(1 if rep.errors else 0)
    rep.emit()
    print(f"checked {n_pages} pages ({n_fm} with front matter): "
          f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    print(coverage_line(rep))
    if args.list_missing_summaries:
        for path in rep.summary_missing:
            print(f"  no summary: {path}")
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()
