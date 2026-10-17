#!/usr/bin/env python3
"""Check the pages you changed, jump to each problem and fix it.

  python3 .docs/tools/page_doctor.py                 # pages changed since dev, interactive
  python3 .docs/tools/page_doctor.py fields/devops   # a page or folder instead
  python3 .docs/tools/page_doctor.py --all --list    # whole repo, just print

It runs validate.py and check_links.py, keeps what concerns the pages in scope
and, for each problem, says what to do about it. Where the fix is mechanical it
can apply it after showing the change:

  - a ../ link           -> the root-absolute link
  - a misspelt or abbreviated tag/subject ("kubernates", "k8s") -> the right one
  - a single-use tag that names a tool -> marked kind: technology

In the interactive list, type a number to open that problem in your editor at
the right line ($VISUAL or $EDITOR; VS Code, vim, nano and others get the line
number), f1 to apply the first fix of problem 1 (f1b for the second), r to
check again and q to quit. Page text is only changed by a fix you confirmed.

--json prints the problems with their fixes as data (for the GUI or scripts).
Standard library only; page_issues() and apply_fix() are the interface.
"""
import argparse
import contextlib
import difflib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_links  # noqa: E402
import new_page  # noqa: E402

ROOT = new_page.ROOT
TOOLS = os.path.dirname(os.path.abspath(__file__))
TAXONOMY_REL = ".docs/metadata/taxonomy.yaml"
CRASH = "(a check crashed)"        # path of the issue made from a crash; never filtered out by scope

LINE_RE = re.compile(r"^(?P<path>[^:\n]+?):(?P<line>\d+): (?P<level>error|warning): (?P<msg>.*)$")
ALT_RE = re.compile(r"^(?P<path>[^:\n]+?): warning: (?P<msg>\d+ picture\(s\) without a description "
                    r"\(lines (?P<lines>[^)]*)\))$")


# ---------- reading the checks ----------

def run_tool(script):
    """Output lines of a check; a crash (traceback) becomes one error line, never a silent gap."""
    r = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, script), "--root", ROOT],
                       capture_output=True, text=True, cwd=ROOT)
    lines = r.stdout.splitlines()
    if "Traceback" in r.stderr:
        lines.append("%s:1: error: %s crashed (%s); its other results are missing"
                     % (CRASH, script, r.stderr.strip().splitlines()[-1]))
    return lines


def parse(tool, lines):
    out = []
    for text in lines:
        m = LINE_RE.match(text)
        if m:
            out.append({"tool": tool, "level": m["level"], "path": m["path"], "line": int(m["line"]),
                        "message": m["msg"]})
            continue
        m = ALT_RE.match(text)
        if m:
            first = re.match(r"\d+", m["lines"])
            out.append({"tool": tool, "level": "warning", "path": m["path"],
                        "line": int(first.group(0)) if first else 1, "message": m["msg"]})
    return out


def changed_paths():
    """Files changed since the branch left dev (committed or not) plus untracked ones; None when git can't say."""
    def git(*a):
        r = subprocess.run(["git", *a], capture_output=True, text=True, cwd=ROOT)
        return r.stdout.splitlines() if r.returncode == 0 else None
    base = next((b for b in ("origin/dev", "dev") if git("rev-parse", "--verify", "-q", b)), None)
    fork = (git("merge-base", "HEAD", base) or [None])[0] if base else None     # where this branch left dev
    diff, fresh = git("diff", "--name-only", fork or "HEAD"), git("ls-files", "--others", "--exclude-standard")
    if diff is None or fresh is None:
        return None
    return set(diff) | set(fresh)


def in_scope(path, scope):
    return scope is None or path == CRASH or any(path == s or path.startswith(s.rstrip("/") + "/") for s in scope)


def read_rel(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", newline="") as f:
        return f.read()


# ---------- text edits (pure functions: text in, text out) ----------

def fm_span(text):
    m = re.match(r"\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
    return (m.start(1), m.end(1)) if m else None


def replace_in_list(text, key, old, new):
    """Replace one value in a one-line `key: [a, b]` list of the front matter ("" removes it); None if not possible."""
    span = fm_span(text)
    if not span:
        return None
    block = text[span[0]:span[1]]
    m = re.search(r"^(%s:\s*\[)([^\]\n]*)(\])" % re.escape(key), block, re.M)
    if not m:
        return None
    items = [x.strip() for x in m.group(2).split(",") if x.strip()]
    if old not in items:
        return None
    out = []
    for x in items:
        x = new if x == old else x
        if x and x not in out:
            out.append(x)
    block = block[:m.start(2)] + ", ".join(out) + block[m.end(2):]
    return text[:span[0]] + block + text[span[1]:]


def tag_block(lines, tag):
    """(start, end) line indexes of a tag's entry in the tags section of taxonomy.yaml, or None."""
    inside = False
    for i, line in enumerate(lines):
        if re.match(r"^\S", line):
            inside = line.split("#")[0].rstrip() == "tags:"
        elif inside and re.match(r"^  %s:\s*$" % re.escape(tag), line):
            end = i + 1
            while end < len(lines) and re.match(r"^    \S", lines[end]):
                end += 1
            return i, end
    return None


def ensure_technology(taxonomy, tag):
    """taxonomy.yaml text with `tag` present and marked kind: technology."""
    lines = taxonomy.splitlines(keepends=True)
    span = tag_block(lines, tag)
    if span:
        if any(re.match(r"^    kind:", l) for l in lines[span[0]:span[1]]):
            return taxonomy
        lines.insert(span[1], "    kind: technology\n")
        return "".join(lines)
    label = " ".join(w.capitalize() for w in tag.split("-"))
    start = next(i for i, l in enumerate(lines) if l.rstrip() == "tags:")
    end = start + 1
    while end < len(lines) and not re.match(r"^\S", lines[end]):
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    pos = end
    for i in range(start + 1, end):
        m = re.match(r"^  ([a-z0-9-]+):\s*$", lines[i])
        if m and m.group(1) > tag:
            pos = i
            break
    lines[pos:pos] = ["  %s:\n" % tag, "    label: %s\n" % label, "    kind: technology\n"]
    return "".join(lines)


def drop_tag(taxonomy, tag):
    lines = taxonomy.splitlines(keepends=True)
    span = tag_block(lines, tag)
    if span:
        del lines[span[0]:span[1]]
    return "".join(lines)


# ---------- suggestions ----------

def numeronym(short, word):
    """k8s ~ kubernetes, i18n ~ internationalization."""
    m = re.fullmatch(r"([a-z])(\d+)([a-z])", short)
    return bool(m) and len(word) == int(m.group(2)) + 2 and word[0] == m.group(1) and word[-1] == m.group(3)


def closest(word, allowed):
    """The allowed value `word` most likely means ("hpc" -> systems-and-hpc), or ""."""
    for a in allowed:
        if word in a.split("-"):
            return a
    near = difflib.get_close_matches(word, allowed, n=1, cutoff=0.7)
    return near[0] if near else ""


def suggest_word(word, pools):
    """The word from `pools` (lists, most trusted first) that `word` is a short form or typo of."""
    best = None
    for rank, pool in enumerate(pools):
        for cand in pool:
            if cand == word or len(cand) < 3:
                continue
            score = 1.0 if numeronym(word, cand) else difflib.SequenceMatcher(None, word, cand).ratio()
            if score >= 0.75 and (best is None or (score, -rank) > best[0]):
                best = ((score, -rank), cand)
    return best[1] if best else ""


def tag_uses(exclude):
    """{tag: number of pages using it}, not counting the page `exclude`."""
    uses = {}
    for pages in new_page.scan().values():
        for rel, _ in pages:
            if rel == exclude:
                continue
            for t in new_page.front_matter(rel).get("tags") or []:
                uses[t] = uses.get(t, 0) + 1
    return uses


def command_fix(label, argv):
    """A fix that runs a command (the generated indexes are rewritten by their generator)."""
    return {"label": label, "safe": False, "files": {}, "run": list(argv)}


def input_fix(label, prompt, build):
    """A fix that needs a typed value first; build(value) returns the real fix (or None)."""
    return {"label": label, "safe": False, "files": {}, "input": prompt, "build": build}


def make_fix(label, files, safe=False):
    """files: {rel: new_text}; entries equal to the current text are dropped."""
    files = {rel: new for rel, new in files.items() if new is not None and new != read_rel(rel)}
    return {"label": label, "safe": safe, "files": files} if files else None


def tag_fixes(issue, tag):
    page = issue["path"]
    text = read_rel(page)
    tax = read_rel(TAXONOMY_REL)
    known = list(new_page.load_tags())
    fm = new_page.front_matter(page)
    heading = next((l[2:] for l in text.splitlines() if l.startswith("# ")), "")
    title_words = re.findall(r"[a-z0-9]+", (heading + " " + os.path.basename(page)[:-3]).lower())
    others = [t for t in (fm.get("tags") or []) if t != tag]
    cand = suggest_word(tag, [title_words, [t for t in known if t != tag], others]) or ""
    fixes = []
    if cand:
        new_text = replace_in_list(text, "tags", tag, cand)
        new_tax = ensure_technology(tax, cand)
        if tag_uses(page).get(tag, 0) == 0:
            new_tax = drop_tag(new_tax, tag)
        why = "numeronym" if numeronym(tag, cand) else "typo"
        fixes.append(make_fix("use tag '%s' instead of '%s' (looks like a %s; '%s' is marked as a technology)"
                              % (cand, tag, "short form" if why == "numeronym" else "misspelling", cand),
                              {page: new_text, TAXONOMY_REL: new_tax}))
    fixes.append(make_fix("keep '%s' and mark it kind: technology (right when it names a concrete tool)" % tag,
                          {TAXONOMY_REL: ensure_technology(tax, tag)}))
    return [f for f in fixes if f]


def enum_fixes(issue, key, value):
    page = issue["path"]
    allowed = list(new_page.load_tags()) if key == "tags" else new_page.load_section("domains")
    guess = closest(value, allowed)
    fixes = []
    if guess:
        fixes.append(make_fix("use '%s' instead of '%s'" % (guess, value),
                              {page: replace_in_list(read_rel(page), key, value, guess)}))
    fixes.append(make_fix("remove '%s' from %s" % (value, key), {page: replace_in_list(read_rel(page), key, value, "")}))
    return [f for f in fixes if f]


def find_by_name(clean):
    """The one repo path (file, folder or page without .md) whose end matches the link, or ""."""
    tail = re.sub(r"^(?:\.{1,2}/)+", "", clean.lstrip("/")).rstrip("/")
    if not tail:
        return ""
    hits = set()
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x not in new_page.SKIP_DIRS]
        rel_dir = os.path.relpath(d, ROOT).replace(os.sep, "/")
        for name in dirs + files:
            rel = name if rel_dir == "." else rel_dir + "/" + name
            for cand in (rel, rel[:-3] if rel.endswith(".md") else None):
                if cand and (cand == tail or cand.endswith("/" + tail)):
                    hits.add(rel if cand == rel else cand)
    return hits.pop() if len(hits) == 1 else ""


def link_fixes(issue, target, what):
    page = issue["path"]
    clean = re.split(r"[?#]", target, 1)[0]
    rest = target[len(clean):]
    resolved = os.path.normpath(os.path.join(os.path.dirname(page), clean)).replace(os.sep, "/")
    exists = os.path.exists(os.path.join(ROOT, resolved)) or os.path.exists(os.path.join(ROOT, resolved + ".md"))
    slash = "/" if clean.endswith("/") else ""
    if what.startswith("relative") and exists:
        new, label, safe = "/" + resolved + slash + rest, "write the link root-absolute", True
    else:
        found = find_by_name(clean)
        if not found:
            return []
        new, label, safe = "/" + found + slash + rest, "the link looks meant for %s (found by name)" % found, False
        if what.startswith("target does not exist") and not clean.startswith("/"):
            return []
    lines = read_rel(page).splitlines(keepends=True)
    n = issue["line"] - 1
    if not (0 <= n < len(lines)) or ("](%s)" % target) not in lines[n]:
        return []
    lines[n] = lines[n].replace("](%s)" % target, "](%s)" % new)
    fix = make_fix("%s: %s" % (label, new), {page: "".join(lines)}, safe=safe)
    return [fix] if fix else []


def describe(issue):
    """Fill in issue["hint"] and issue["fixes"] (a list of {label, safe, files})."""
    msg, hint, fixes = issue["message"], "", []
    m = re.match(r"tag '([^']+)' is used by only one page", msg)
    if m:
        hint = "A tag needs 2+ pages, or must name a concrete tool. Fix the spelling, merge it into a tag you already use, or mark it as a technology."
        fixes = tag_fixes(issue, m.group(1))
    m = re.match(r"invalid (domain|tag) '([^']+)'", msg)
    if m:
        key = "domains" if m.group(1) == "domain" else "tags"
        hint = ("Not in .docs/metadata/taxonomy.yaml. Use a known value, or add it there first."
                + (" (\"technology\" is not a tag: it is the kind: technology marker inside taxonomy.yaml.)"
                   if m.group(2) == "technology" else ""))
        fixes = enum_fixes(issue, key, m.group(2))
    if issue["tool"] == "check_links" and issue["level"] == "error":
        target, _, what = msg.partition(": ")
        if what.startswith(("relative link", "target does not exist")):
            hint = ("Docsify resolves ./ and ../ links against the site root, so write the path from the root."
                    if what.startswith("relative") else "The linked file or folder is not there; check the name.")
            fixes = link_fixes(issue, target, what)
    if "picture(s) without a description" in msg:
        hint = "Write what each picture shows between the brackets: ![what it shows](path). Screen readers and search use it."
    if issue["tool"] == "page":
        if msg.startswith("relative link"):
            hint = "Write the links from the site root, e.g. /fields/x/page.md (python3 .docs/tools/check_links.py names the lines)."
        elif msg.startswith(("no front matter", "no summary", "no type", "no domains", "no tags", "no level")):
            hint = ("Run python3 .docs/tools/new_page.py --adopt %s to be asked for the missing fields." % issue["path"]
                    if hasattr(new_page, "adopt") else "Add it to the front matter (CLAUDE.md section 21).")
        else:
            hint = "See python3 .docs/tools/new_page.py --check %s." % issue["path"]
    if issue["path"] == CRASH:
        hint = "Fix the crash first: until then this check reports nothing. Often the branch is behind dev, or a page uses a field the checker does not know yet."
    issue["hint"], issue["fixes"] = hint, fixes
    return issue


def page_todos(rel):
    """The "To do" items of new_page.py --check for one page, as issues."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            new_page.check_page(rel)
        except SystemExit:
            return []
    out, inside = [], False
    for line in buf.getvalue().splitlines():
        if line.strip() == "To do:":
            inside = True
        elif inside and line.startswith("  - "):
            out.append({"tool": "page", "level": "todo", "path": rel, "line": 1, "message": line[4:]})
    return out


def pages_in(scope):
    """Content pages named by the scope (files, or folders searched); none for the whole repo."""
    pages = set()
    for entry in scope or []:
        full = os.path.join(ROOT, entry)
        if os.path.isdir(full):
            for d, dirs, files in os.walk(full):
                dirs[:] = [x for x in dirs if not x.startswith(".")]
                pages |= {os.path.relpath(os.path.join(d, f), ROOT).replace(os.sep, "/") for f in files if f.endswith(".md")}
        elif entry.endswith(".md") and os.path.isfile(full):
            pages.add(entry)
    return sorted(p for p in pages if not p.endswith("README.md") and "/" in p
                  and not any(part.startswith(".") for part in p.split("/")))      # .docs, .github, .claude ...


def snapshot(folder):
    out = {}
    for d, _, files in os.walk(os.path.join(ROOT, folder)):
        for f in files:
            full = os.path.join(d, f)
            with open(full, "rb") as fh:
                out[full] = fh.read()
    return out


def stale_index_issue(scope):
    """An issue when .docs/generated differs from what generate_index.py writes now (CI fails on that)."""
    if scope is not None and not any(p.endswith(".md") or p == TAXONOMY_REL for p in scope):
        return []
    if not os.path.isdir(os.path.join(ROOT, ".docs", "generated")):
        return []
    before = snapshot(".docs/generated")
    try:
        r = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "generate_index.py"), "--root", ROOT],
                           capture_output=True, text=True, cwd=ROOT)
        after = snapshot(".docs/generated")
    finally:                                     # leave the files as they were: only the fix changes them
        now = snapshot(".docs/generated")
        for full in set(now) - set(before):
            os.remove(full)
        for full, data in before.items():
            if now.get(full) != data:
                with open(full, "wb") as fh:
                    fh.write(data)
    if r.returncode or before == after:
        return []
    names = sorted({os.path.relpath(f, ROOT).replace(os.sep, "/") for f in set(before) | set(after) if before.get(f) != after.get(f)})
    return [{"tool": "index", "level": "error", "path": ".docs/generated", "line": 1,
             "message": "the generated indexes are stale (%d file(s) differ: %s); CI fails on this"
                        % (len(names), ", ".join(names[:3]) + (", ..." if len(names) > 3 else "")),
             "hint": "They are rewritten from the pages' front matter. Commit them with the change.",
             "fixes": [command_fix("regenerate them (python3 .docs/tools/generate_index.py)",
                                   [sys.executable, "-I", os.path.join(TOOLS, "generate_index.py"), "--root", ROOT])]}]


def alt_fix(rel, line, k):
    """A fix asking for a description of the k-th picture without one on `line`."""
    def build(value):
        value = " ".join(value.replace("[", "(").replace("]", ")").split())
        if not value:
            return None
        lines = read_rel(rel).splitlines(keepends=True)
        if not 0 < line <= len(lines):
            return None
        hits = [m for m in check_links.IMAGE_ALT_RE.finditer(lines[line - 1]) if check_links.NO_ALT_RE.match(m.group(1).strip())]
        if k >= len(hits):
            return None
        m = hits[k]
        lines[line - 1] = lines[line - 1][:m.start(1)] + value + lines[line - 1][m.end(1):]
        return make_fix("describe the picture: " + value, {rel: "".join(lines)})
    return input_fix("describe it", "What does the picture show? (a few words)", build)


def picture_issues(scope):
    """One issue per picture without a description, each with a fix that asks for the description."""
    out = []
    for page, lines in sorted(check_links.alt_report(ROOT).items()):
        if not in_scope(page, scope):
            continue
        text = read_rel(page).splitlines()
        seen = {}
        for n in lines:
            k = seen[n] = seen.get(n, -1) + 1
            shown = text[n - 1].strip()[:90] if 0 < n <= len(text) else ""
            out.append({"tool": "check_links", "level": "todo", "path": page, "line": n,
                        "message": "picture without a description: " + shown,
                        "hint": "Write what the picture shows between the brackets: ![what it shows](path). Screen readers and search use it.",
                        "fixes": [alt_fix(page, n, k)]})
    return out


def readme_swap_issues(scope):
    """A folder README whose title belongs to its subfolder while the subfolder's README belongs to the folder."""
    readmes = {}
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x not in new_page.SKIP_DIRS]
        if "README.md" in files:
            readmes[os.path.relpath(d, ROOT).replace(os.sep, "/")] = os.path.join(d, "README.md")

    def overlap(rel_dir, folder_name):
        head = new_page.front_matter(rel_dir + "/README.md").get("sidebar_label", "") if rel_dir != "." else ""
        title = " ".join([head, new_page.first_h1(readmes[rel_dir])])
        return len(new_page.words(title) & new_page.words(folder_name.replace("-", " ")))
    out = []
    for parent in readmes:
        if parent == ".":
            continue
        for child in readmes:
            if os.path.dirname(child) != parent:
                continue
            pn, cn = os.path.basename(parent), os.path.basename(child)
            if overlap(parent, pn) == 0 and overlap(parent, cn) > 0 and overlap(child, cn) == 0 and overlap(child, pn) > 0:
                p_rel, c_rel = parent + "/README.md", child + "/README.md"
                if not (in_scope(p_rel, scope) or in_scope(c_rel, scope)):
                    continue
                out.append({"tool": "layout", "level": "warning", "path": p_rel, "line": 1,
                            "message": "%s is about %s and %s is about %s: the two README files look swapped"
                                       % (p_rel, cn, c_rel, pn),
                            "hint": "Each README should describe its own folder; otherwise the sidebar nests the topics the wrong way round.",
                            "fixes": [make_fix("swap the two README files", {p_rel: read_rel(c_rel), c_rel: read_rel(p_rel)})]})
    return [i for i in out if i["fixes"][0]]


def page_issues(scope=None, pictures=False):
    """All problems for the pages in scope (a set of paths/folders; None = whole repo), with fixes."""
    found = parse("validate", run_tool("validate.py")) + parse("check_links", run_tool("check_links.py"))
    found = [i for i in found if in_scope(i["path"], scope)]
    if pictures:        # one issue per picture instead of one line per page
        found = [i for i in found if "picture(s) without a description" not in i["message"]] + picture_issues(scope)
    for rel in pages_in(scope):
        found += page_todos(rel)
    found += readme_swap_issues(scope) + stale_index_issue(scope)
    order = {"error": 0, "warning": 1, "todo": 2}
    found.sort(key=lambda i: (order[i["level"]], i["path"], i["line"]))
    return [i if "fixes" in i else describe(i) for i in found]


# ---------- applying and opening ----------

def diff_of(fix):
    if fix.get("run"):
        return "will run: " + " ".join(fix["run"])
    if fix.get("input"):
        return "needs: " + fix["input"]
    out = []
    for rel, new in fix["files"].items():
        out += difflib.unified_diff(read_rel(rel).splitlines(), new.splitlines(), "a/" + rel, "b/" + rel,
                                    lineterm="", n=1)
    return "\n".join(out)


def fix_summary(fix):
    """A fix as plain data (for --json and the GUI)."""
    return {"label": fix["label"], "safe": fix["safe"], "files": sorted(fix["files"]), "diff": diff_of(fix),
            "run": fix.get("run"), "input": fix.get("input")}


def apply_fix(fix, value=None):
    """Write the fix's files (each all or nothing) or run its command. Returns what was changed."""
    if fix.get("input"):
        fix = fix["build"](value or "")
        if not fix:
            raise ValueError("that value gives no change")
    if fix.get("run"):
        r = subprocess.run(fix["run"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("%s failed: %s" % (" ".join(fix["run"]), (r.stderr or r.stdout).strip()[-300:]))
        return [" ".join(fix["run"])]
    for rel, new in fix["files"].items():
        full = os.path.join(ROOT, rel)
        tmp = full + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        os.replace(tmp, full)
    return list(fix["files"])


def editor_command(path, line, env=None):
    """argv that opens `path` at `line` in $VISUAL/$EDITOR (VS Code if nothing is set), and whether it blocks."""
    env = os.environ if env is None else env
    spec = env.get("VISUAL") or env.get("EDITOR") or ""
    if not spec:
        spec = "code" if env.get("TERM_PROGRAM") == "vscode" and shutil.which("code") else \
            next((e for e in ("nano", "vim", "vi") if shutil.which(e)), "")
    if not spec:
        return None, False
    argv = shlex.split(spec)
    exe = os.path.basename(argv[0])
    if exe in ("code", "code-insiders", "codium", "cursor", "windsurf"):
        return argv + ["--goto", "%s:%d" % (path, line)], False
    if exe in ("subl", "sublime_text", "hx", "helix", "zed"):
        return argv + ["%s:%d" % (path, line)], exe in ("hx", "helix")
    if exe in ("vim", "nvim", "vi", "nano", "micro", "emacs", "emacsclient", "kak", "joe", "ne"):
        return argv + ["+%d" % line, path], True
    return argv + [path], True


def open_issue(issue):
    argv, blocks = editor_command(os.path.join(ROOT, issue["path"]), issue["line"])
    if not argv:
        print("  No editor found. Set one, e.g.  export EDITOR=nano   (or open %s:%d yourself)"
              % (issue["path"], issue["line"]))
        return False
    try:
        subprocess.run(argv, cwd=ROOT)
    except OSError as e:
        print("  Could not start %s: %s" % (argv[0], e))
        return False
    return blocks


# ---------- output ----------

def show(issues, scope):
    if not issues:
        print("Nothing to fix%s." % (" in %d changed file(s)" % len(scope) if scope else ""))
        return
    print("%d problem(s):\n" % len(issues))
    for n, i in enumerate(issues, 1):
        print("%2d. [%s] %s:%d\n    %s" % (n, i["level"], i["path"], i["line"], i["message"]))
        if i["hint"]:
            print("    -> " + i["hint"])
        for k, f in enumerate(i["fixes"]):
            print("    fix %d%s: %s%s" % (n, "abcdefgh"[k], f["label"], "  [safe]" if f["safe"] else ""))
    print()


def interactive(scope, pictures=False):
    issues = page_issues(scope, pictures)
    while True:
        show(issues, scope)
        if not issues:
            return 0
        try:
            cmd = input("number = open in editor, f<n>[letter] = apply a fix, r = check again, q = quit: ").strip().lower()
        except EOFError:
            return 1
        if cmd in ("q", "quit", ""):
            return 1
        if cmd in ("r", "re"):
            issues = page_issues(scope, pictures)
            continue
        m = re.fullmatch(r"(f)?(\d+)([a-h]?)", cmd)
        if not m or not 0 < int(m[2]) <= len(issues):
            print("  not a choice\n")
            continue
        issue = issues[int(m[2]) - 1]
        if not m[1]:
            if open_issue(issue):
                issues = page_issues(scope, pictures)        # a terminal editor has closed: look again
            else:
                print("  Save the file, then type r to check again.\n")
            continue
        k = "abcdefgh".index(m[3] or "a")
        if k >= len(issue["fixes"]):
            print("  no such fix; this problem has %d\n" % len(issue["fixes"]))
            continue
        fix, value = issue["fixes"][k], None
        if fix.get("input"):
            value = input(fix["input"] + " ").strip()
            fix = fix["build"](value)
            if not fix:
                print("  nothing to change\n")
                continue
        print("\n" + diff_of(fix) + "\n")
        if input("Apply this change? [y/N] ").strip().lower().startswith("y"):
            try:
                print("  changed: " + ", ".join(apply_fix(fix)) + "\n")
            except (RuntimeError, ValueError) as e:
                print("  %s\n" % e)
            issues = page_issues(scope, pictures)


# ---------- git hook ----------

HOOK_MARK = "# installed by page_doctor.py --install-hook"
HOOK = """#!/bin/sh
%s
# Stops a push when the checks find an error in what this branch changed.
# Skip it once with: git push --no-verify
exec python3 "$(git rev-parse --show-toplevel)/.docs/tools/page_doctor.py" --pre-push
""" % HOOK_MARK


def hook_path():
    r = subprocess.run(["git", "rev-parse", "--git-path", "hooks/pre-push"], capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        sys.exit("error: not a git repository")
    return os.path.join(ROOT, r.stdout.strip())


def install_hook():
    path = hook_path()
    if os.path.exists(path) and HOOK_MARK not in new_page.read(path):
        sys.exit("error: %s already exists and was not made by this tool; add the line yourself:\n  "
                 "python3 .docs/tools/page_doctor.py --pre-push || exit 1" % path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(HOOK)
    os.chmod(path, 0o755)
    print("Installed %s\nA push now stops on errors in the files your branch changed. Skip once: git push --no-verify" % path)


def uninstall_hook():
    path = hook_path()
    if os.path.exists(path) and HOOK_MARK in new_page.read(path):
        os.remove(path)
        print("Removed " + path)
    else:
        print("No hook from this tool at " + path)


def pre_push():
    """Exit 1 on errors (validation, broken links, stale indexes, a crashed check) in the changed files."""
    scope = changed_paths()
    errors = [i for i in page_issues(scope) if i["level"] == "error"]
    if not errors:
        return 0
    show(errors, scope)
    print("Fix these (python3 .docs/tools/page_doctor.py), or skip once with: git push --no-verify")
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check changed pages, jump to each problem, apply fixes.")
    ap.add_argument("paths", nargs="*", help="pages or folders to check (default: files changed since dev)")
    ap.add_argument("--all", action="store_true", help="the whole repository")
    ap.add_argument("--list", action="store_true", help="print the problems and exit (1 if any)")
    ap.add_argument("--json", action="store_true", help="print the problems with their fixes as JSON and exit")
    ap.add_argument("--pictures", action="store_true", help="list each picture without a description (a fix asks for the text)")
    ap.add_argument("--errors-only", action="store_true", help="leave out warnings and to-dos")
    ap.add_argument("--apply-safe", action="store_true", help="apply every fix marked [safe] without asking")
    ap.add_argument("--pre-push", action="store_true", help="what the git hook runs: exit 1 on errors in the changed files")
    ap.add_argument("--install-hook", action="store_true", help="install a git pre-push hook that runs --pre-push")
    ap.add_argument("--uninstall-hook", action="store_true", help="remove the hook this tool installed")
    args = ap.parse_args(argv)
    if args.install_hook:
        return install_hook()
    if args.uninstall_hook:
        return uninstall_hook()
    if args.pre_push:
        return pre_push()
    if args.all:
        scope = None
    elif args.paths:
        scope = {os.path.relpath(os.path.abspath(p), ROOT).replace(os.sep, "/") for p in args.paths}
    else:
        scope = changed_paths()
        if scope is None:
            sys.exit("error: could not ask git what changed; pass paths or --all")
    if args.apply_safe:
        for issue in page_issues(scope, args.pictures):
            fix = next((f for f in issue["fixes"] if f["safe"]), None)
            if fix:
                print("fixed %s:%d  %s" % (issue["path"], issue["line"], fix["label"]))
                apply_fix(fix)
    issues = page_issues(scope, args.pictures)
    if args.errors_only:
        issues = [i for i in issues if i["level"] == "error"]
    if args.json:
        print(json.dumps([dict(i, fixes=[fix_summary(f) for f in i["fixes"]]) for i in issues], indent=2))
        return 1 if issues else 0
    if args.list or args.errors_only or not sys.stdin.isatty():
        show(issues, scope)
        return 1 if issues else 0
    return interactive(scope, args.pictures)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit("\nStopped.")
