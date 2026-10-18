#!/usr/bin/env python3
"""Run every repository check in one go: the validation suite.

Steps, in order:
  1. validate.py        front matter (ids, relations, order, labels), 0 errors
  2. check_links.py     internal links and unsafe HTML, 0 broken
  3. generated output   .docs/generated, _sidebar.md and _navbar.md are what
                        the generators produce from the current files
  4. the test_*.py files next to this script

Without --fix a stale step 3 fails the run and nothing on disk changes.
With --fix the generators are left applied, so one command finishes a change:
    python3 .docs/tools/check_all.py --fix

Usage: python3 .docs/tools/check_all.py [--fix] [--skip-tests]
"""
import argparse
import glob
import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(TOOLS))
DOCS = os.path.join(ROOT, ".docs")
GENERATED = os.path.join(DOCS, "generated")
NAV_FILES = ("_sidebar.md", "_navbar.md")


def run(label, cmd, cwd=ROOT):
    """Run one command quietly; print its output only when it fails."""
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    ok = r.returncode == 0
    print(f"[{'ok' if ok else 'FAIL'}] {label}")
    if not ok:
        print((r.stdout + r.stderr).rstrip())
    return ok


def snapshot():
    """{path: bytes} of every file the generators write."""
    files = {}
    for base, _, names in os.walk(GENERATED):
        for n in names:
            p = os.path.join(base, n)
            files[p] = open(p, "rb").read()
    for n in NAV_FILES:
        p = os.path.join(DOCS, n)
        if os.path.exists(p):
            files[p] = open(p, "rb").read()
    return files


def regenerate():
    ok = run("generate_index.py", [sys.executable, "-I", os.path.join(TOOLS, "generate_index.py")])
    ok = run("gen_sidebar.sh", ["./gen_sidebar.sh"], cwd=DOCS) and ok
    ok = run("gen_navbar.sh", ["./gen_navbar.sh"], cwd=DOCS) and ok
    return ok


def check_generated(fix):
    before = snapshot()
    if not regenerate():
        return False
    after = snapshot()
    stale = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    if stale and not fix:
        for p in set(before) | set(after):          # put the tree back as it was
            if p in before:
                open(p, "wb").write(before[p])
            elif os.path.exists(p):
                os.remove(p)
    for p in stale:
        print("  %s %s" % ("updated" if fix else "stale  ", os.path.relpath(p, ROOT)))
    ok = fix or not stale
    print(f"[{'ok' if ok else 'FAIL'}] generated files up to date" + (" (regenerated)" if stale and fix else ""))
    if not ok:
        print("  run: python3 .docs/tools/check_all.py --fix   and commit the result")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fix", action="store_true", help="leave regenerated indexes, sidebar and navbar in place")
    ap.add_argument("--skip-tests", action="store_true", help="skip the test_*.py files")
    args = ap.parse_args()

    py = [sys.executable, "-I"]
    results = [run("validate.py", py + [os.path.join(TOOLS, "validate.py")]),
               run("check_links.py", py + [os.path.join(TOOLS, "check_links.py")])]
    if results[0]:   # the generators refuse to run on invalid front matter
        results.append(check_generated(args.fix))
    else:
        print("[skip] generated files (fix the validation errors first)")
        results.append(False)
    if not args.skip_tests:
        for t in sorted(glob.glob(os.path.join(TOOLS, "test_*.py"))):
            results.append(run(os.path.basename(t), py + [t]))

    failed = results.count(False)
    print("\nAll checks passed." if not failed else f"\n{failed} check(s) failed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
