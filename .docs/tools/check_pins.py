#!/usr/bin/env python3
"""Compare the versions pinned in index.html with the latest npm releases.

Reads every cdn.jsdelivr.net/npm/<package>@<version> URL in index.html and in
the site scripts .docs/*.js (some libraries load only when a page needs them), asks
the npm registry for the latest version, its release date and any deprecation
notice, and prints a table. It never changes anything.

Exit codes: 0 = table printed, 1 = a pin is deprecated or an address is not
pinned to an exact version. Behind-the-latest is information, not a failure.

Usage: python3 .docs/tools/check_pins.py [--markdown]
Standard library only; needs network access.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URL_RE = re.compile(r"(?:https?:)?//(?:cdn\.jsdelivr\.net/npm|unpkg\.com)/((?:@[\w.-]+/)?[\w.-]+)(@[^/\"']*)?")


def pins(html):
    found = {}
    for name, ver in URL_RE.findall(html):
        found.setdefault(name, set()).add(ver[1:] if ver else "")
    return found


def latest(name):
    url = "https://registry.npmjs.org/" + quote(name, safe="@")
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.load(r)
    ver = data["dist-tags"]["latest"]
    return ver, data["time"].get(ver, "")[:10], data["versions"][ver].get("deprecated", "")


def site_sources():
    """index.html plus the site's own scripts, as one text."""
    docs = os.path.join(ROOT, ".docs")
    files = [os.path.join(ROOT, "index.html")] + sorted(
        os.path.join(docs, n) for n in os.listdir(docs) if n.endswith(".js"))
    text = []
    for path in files:
        with open(path, encoding="utf-8") as f:
            text.append(f.read())
    return "\n".join(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--markdown", action="store_true", help="print a markdown table (for a job summary)")
    args = ap.parse_args()
    found = pins(site_sources())

    rows, bad = [], 0
    for name in sorted(found):
        for pinned in sorted(found[name]):
            note = ""
            if not re.fullmatch(r"\d+\.\d+\.\d+", pinned):
                note, bad = "NOT PINNED to an exact version", bad + 1
            try:
                ver, date, dep = latest(name)
            except Exception as e:  # network or registry trouble: report, do not fail the check
                rows.append((name, pinned or "-", "?", "", "registry error: %s" % e))
                continue
            if dep:
                note, bad = "DEPRECATED: " + dep[:80], bad + 1
            elif pinned and pinned != ver and not note:
                note = "behind"
            rows.append((name, pinned or "-", ver, date, note or "current"))

    head = ("package", "pinned", "latest", "released", "status")
    if args.markdown:
        print("| " + " | ".join(head) + " |\n|" + "---|" * len(head))
        for r in rows:
            print("| " + " | ".join(r) + " |")
    else:
        widths = [max(len(str(x)) for x in col) for col in zip(head, *rows)]
        for r in [head] + rows:
            print("  ".join(str(x).ljust(w) for x, w in zip(r, widths)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
