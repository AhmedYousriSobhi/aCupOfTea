#!/usr/bin/env python3
"""Compare the versions pinned in index.html with the latest npm releases.

Reads every cdn.jsdelivr.net/npm/<package>@<version> URL in index.html and in
the site scripts .docs/*.js (some libraries load only when a page needs them), asks
the npm registry for the latest version, its release date and any deprecation
notice, and prints a table. It never changes anything.

Exit codes: 0 = table printed, 1 = a pin is deprecated or an address is not
pinned to an exact version. Behind-the-latest is information, not a failure.

With --sri it instead checks the integrity hashes: every CDN <script>/<link>
in index.html, and every ['address', 'hash'] pair in .docs/*.js, must carry a
sha384 hash that matches the file the CDN serves today (exit 1 otherwise).
Add --write to fill in or correct the hashes (after bumping a version).

Usage: python3 .docs/tools/check_pins.py [--markdown] [--sri [--write]]
Standard library only; needs network access.
"""
import argparse
import base64
import hashlib
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


CDN = r"(?:https?:)?//(?:cdn\.jsdelivr\.net/npm|unpkg\.com)/[^\"' ]+"
TAG_RE = re.compile(r"<(?:script|link)\b[^>]*?(?:src|href)=\"(" + CDN + r")\"[^>]*>")
PAIR_RE = re.compile(r"\[\s*'(" + CDN + r")'\s*,\s*'([^']*)'\s*\]")
INTEGRITY_RE = re.compile(r'\s+integrity="([^"]*)"')


def sri(url):
    """sha384 integrity value of the file at url, as the browser computes it."""
    url = "https:" + url if url.startswith("//") else url
    with urllib.request.urlopen(url, timeout=30) as r:
        return "sha384-" + base64.b64encode(hashlib.sha384(r.read()).digest()).decode()


def sri_tag(tag, url, want):
    """The tag with integrity set to want and crossorigin present."""
    tag = INTEGRITY_RE.sub("", tag)
    tag = re.sub(r'\s+crossorigin(="[^"]*")?', "", tag)
    end = "/>" if tag.endswith("/>") else ">"
    return tag[: -len(end)].rstrip() + f' integrity="{want}" crossorigin="anonymous"' + end


def check_sri(write):
    """Compare (and with write, fix) every integrity hash. Returns rows and the failure count."""
    docs = os.path.join(ROOT, ".docs")
    files = ["index.html"] + sorted(".docs/" + n for n in os.listdir(docs) if n.endswith(".js"))
    rows, bad, cache = [], 0, {}

    def want(url):
        if url not in cache:
            cache[url] = sri(url)
        return cache[url]

    for rel in files:
        path = os.path.join(ROOT, rel)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        found = []  # (match, url, current hash)
        for m in TAG_RE.finditer(text):
            cur = INTEGRITY_RE.search(m.group(0))
            found.append((m, m.group(1), cur.group(1) if cur else ""))
        for m in PAIR_RE.finditer(text):
            found.append((m, m.group(1), m.group(2)))
        new, shift = text, 0
        for m, url, cur in found:
            try:
                good = want(url)
            except Exception as e:
                rows.append((rel, url, f"fetch error: {e}"))
                bad += 1
                continue
            status = "ok" if cur == good else ("missing" if not cur else "MISMATCH")
            if status != "ok":
                if write:
                    if m.re is TAG_RE:
                        rep = sri_tag(m.group(0), url, good)
                    else:
                        rep = f"['{url}', '{good}']"
                    a, b = m.start() + shift, m.end() + shift
                    new = new[:a] + rep + new[b:]
                    shift += len(rep) - (m.end() - m.start())
                    status += " -> written"
                else:
                    bad += 1
            rows.append((rel, url, status))
        if new != text:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new)
    return rows, bad


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
    ap.add_argument("--sri", action="store_true", help="check the integrity hashes instead of the versions")
    ap.add_argument("--write", action="store_true", help="with --sri: fill in or correct the hashes")
    args = ap.parse_args()
    if args.sri:
        rows, bad = check_sri(args.write)
        if args.markdown:
            print("| file | address | integrity |\n|---|---|---|")
            for r in rows:
                print("| " + " | ".join(r) + " |")
        else:
            for r in rows:
                print("  ".join(r))
        return 1 if bad else 0
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
