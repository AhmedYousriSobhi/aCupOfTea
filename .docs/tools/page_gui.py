#!/usr/bin/env python3
"""A local page for creating, completing and fixing pages, in your browser.

  python3 .docs/tools/new_page.py --gui      # or: python3 .docs/tools/page_gui.py

It starts a small web server that listens on this computer only (127.0.0.1, a
random port), prints the address and opens it. Three tabs:

  New page          the questions of new_page.py as a form: folder suggestions as you
                    type the title, a warning about similar pages, subjects and tags
                    (new ones can be added), preview, create
  Adopt a page      front matter and index link for a page you wrote by hand
  Fix problems      the list of page_doctor.py: open a problem in your editor at its
                    line, see a suggested fix as a diff, apply it

The form only fills in the options of new_page.py and runs it, so the rules are
the same as in the terminal. Every request must carry a random token and a local
Host header, so another web page or another computer cannot drive it. Stop it
with Ctrl+C or the Close button. Standard library only.
"""
import contextlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from secrets import token_urlsafe
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import new_page  # noqa: E402
import page_doctor  # noqa: E402

LOCK = threading.Lock()          # the tools print and write files: one request at a time
MAX_BODY = 1 << 20
FIELDS = ("summary", "type", "domains", "tags", "level")


# ---------- what the form needs ----------

def taxonomy_types():
    out, inside = [], False
    for line in new_page.read(new_page.TAXONOMY).splitlines():
        if re.match(r"^\S", line):
            inside = line.split("#")[0].rstrip() == "types:"
            continue
        m = inside and re.match(r"^  ([a-z0-9-]+):\s*(.*)$", line)
        if m:
            out.append({"key": m.group(1), "description": m.group(2)})
    return out


def taxonomy_domains():
    out, current, inside = [], None, False
    for line in new_page.read(new_page.TAXONOMY).splitlines():
        if re.match(r"^\S", line):
            inside = line.split("#")[0].rstrip() == "domains:"
            continue
        m = inside and re.match(r"^  ([a-z0-9-]+):\s*$", line)
        if m:
            current = {"key": m.group(1), "label": m.group(1), "description": ""}
            out.append(current)
            continue
        m = inside and current and re.match(r"^    (label|description):\s*(.*?)\s*$", line)
        if m:
            current[m.group(1)] = m.group(2).strip("\"'")
    return out


def page_ids(folders):
    out = []
    for pages in folders.values():
        for rel, h1 in pages:
            pid = new_page.front_matter(rel).get("id")
            if pid:
                out.append({"id": pid, "title": h1 or pid, "path": rel})
    return sorted(out, key=lambda p: p["id"])


def options(title="", folder=""):
    """Everything the form offers, and suggestions for the title and folder typed so far."""
    folders = new_page.scan()
    folder = folder.strip("/")
    types = new_page.neighbours(folder, folders, "type") if folder in folders else []
    return {
        "folders": sorted(folders),
        "suggested_folders": new_page.suggest_folders(title, folders) if title.strip() else [],
        "folder_exists": os.path.isdir(os.path.join(new_page.ROOT, folder)) if folder else None,
        "slug": new_page.slug(title),
        "similar": [{"path": r, "title": h} for r, h in new_page.similar_pages(title, folders)] if title.strip() else [],
        "default_type": types[:1] or ["concept"],
        "default_domains": new_page.default_domains(folder, folders, title)[:new_page.MAX_DOMAINS] if folder else [],
        "types": taxonomy_types(),
        "domains": taxonomy_domains(),
        "tags": [{"key": k, "label": v} for k, v in sorted(new_page.load_tags().items())],
        "levels": list(new_page.LEVELS),
        "pages": page_ids(folders),
        "limits": {"types": new_page.MAX_TYPES, "domains": new_page.MAX_DOMAINS, "tags": new_page.MAX_TAGS},
    }


def adoptable():
    """Pages with something missing from their front matter, with the fields they already have."""
    out = []
    for pages in new_page.scan().values():
        for rel, h1 in pages:
            if os.path.basename(rel) == "README.md":
                continue
            fm = new_page.front_matter(rel)
            missing = [k for k in FIELDS if not fm.get(k)]
            if missing:
                out.append({"path": rel, "title": h1, "have": [k for k in FIELDS if fm.get(k)], "missing": missing})
    return sorted(out, key=lambda p: p["path"])


# ---------- running new_page.py ----------

def run_cli(argv):
    """Run new_page.main with --yes, catching what it prints. Returns {ok, output}."""
    buf = io.StringIO()
    code = 0
    with LOCK, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            new_page.main(list(argv) + ["--yes"])
        except SystemExit as e:
            if isinstance(e.code, int):
                code = e.code
            elif e.code:
                print(e.code)
                code = 1
    return {"ok": not code, "output": buf.getvalue().strip()}


def csv(values):
    return ",".join(str(v).strip() for v in values or [] if str(v).strip())


def meta_argv(d):
    argv = ["--summary", " ".join(str(d.get("summary") or "").split()),
            "--domains", csv(d.get("domains")), "--tags", csv(d.get("tags")),
            "--prerequisites", csv(d.get("prerequisites")), "--related", csv(d.get("related"))]
    if d.get("types"):
        argv += ["--type", csv(d["types"])]
    if d.get("level"):
        argv += ["--level", d["level"]]
    for n in d.get("new_domains") or []:
        argv += ["--new-domain", "%s=%s" % (new_page.slug(n.get("key", "")), n.get("description", ""))]
    for n in d.get("new_tags") or []:
        argv += ["--new-tag", "%s=%s" % (new_page.slug(n.get("key", "")), n.get("label", ""))]
    return argv


def checked(result, page):
    """Add the --check report of a page to a successful result."""
    if result["ok"] and page:
        result["page"] = page
        result["check"] = check_report(page)
    return result


def check_report(page):
    buf = io.StringIO()
    with LOCK, contextlib.redirect_stdout(buf):
        try:
            new_page.check_page(page)
        except SystemExit as e:
            print(e.code)
    return buf.getvalue().strip()


def create(d):
    folder, name = str(d.get("folder", "")).strip("/"), new_page.slug(d.get("name") or d.get("title", ""))
    argv = ["--title", str(d.get("title", "")).strip(), "--folder", folder, "--name", name] + meta_argv(d)
    if d.get("create_folder"):
        argv.append("--create-folder")
    if d.get("dry_run"):
        argv.append("--dry-run")
    result = run_cli(argv)
    return result if d.get("dry_run") else checked(result, "%s/%s.md" % (folder, name))


def adopt(d):
    page = str(d.get("page", "")).strip("/")
    argv = ["--adopt", page] + meta_argv(d) + (["--dry-run"] if d.get("dry_run") else [])
    result = run_cli(argv)
    return result if d.get("dry_run") else checked(result, page)


# ---------- problems ----------

def scope_of(name):
    """"changed" (since dev), "all", or a page/folder path -> scope for page_doctor."""
    if name in ("", "changed", None):
        return page_doctor.changed_paths()
    if name == "all":
        return None
    return {name.strip("/")}


def issue_id(i):
    return "%s:%d:%s" % (i["path"], i["line"], i["message"])


def issues(scope_name, pictures=False):
    with LOCK:
        found = page_doctor.page_issues(scope_of(scope_name), pictures)
    return [dict(i, id=issue_id(i), fixes=[page_doctor.fix_summary(f) for f in i["fixes"]]) for i in found]


def fix(d):
    with LOCK:
        found = page_doctor.page_issues(scope_of(d.get("scope")), bool(d.get("pictures")))
        issue = next((i for i in found if issue_id(i) == d.get("id")), None)
        n = d.get("fix")
        if issue is None or not isinstance(n, int) or not 0 <= n < len(issue["fixes"]):
            return {"ok": False, "output": "That problem has changed since the list was made. Refresh and try again."}
        try:
            written = page_doctor.apply_fix(issue["fixes"][n], d.get("value"))
        except (RuntimeError, ValueError) as e:
            return {"ok": False, "output": str(e)}
    return {"ok": True, "output": "Changed: " + ", ".join(written)}


def open_in_editor(d):
    path = os.path.realpath(os.path.join(new_page.ROOT, str(d.get("path", ""))))
    if not path.startswith(os.path.realpath(new_page.ROOT) + os.sep) or not os.path.isfile(path):
        return {"ok": False, "output": "No such page."}
    argv, blocks = page_doctor.editor_command(path, int(d.get("line") or 1))
    if not argv:
        return {"ok": False, "output": "No editor found. Set one, e.g. export EDITOR=nano, or open the file yourself."}
    if blocks:   # a terminal editor cannot open from a browser
        return {"ok": False, "command": shlex.join(argv),
                "output": "That editor runs in a terminal. Run it there:\n  " + shlex.join(argv)}
    subprocess.Popen(argv, cwd=new_page.ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"ok": True, "output": "Opened in " + os.path.basename(argv[0])}


# ---------- the server ----------

GET_ROUTES = {
    "/api/options": lambda q: options(q.get("title", [""])[0], q.get("folder", [""])[0]),
    "/api/adoptable": lambda q: adoptable(),
    "/api/issues": lambda q: issues(q.get("scope", ["changed"])[0], q.get("pictures", [""])[0] == "1"),
    "/api/check": lambda q: {"output": check_report(q.get("page", [""])[0])},
}
POST_ROUTES = {"/api/create": create, "/api/adopt": adopt, "/api/fix": fix, "/api/open": open_in_editor}


class Handler(BaseHTTPRequestHandler):
    server_version = "page-gui"

    def log_message(self, *args):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(data)

    def allowed(self):
        """A local Host header (stops DNS rebinding) for everything, and the token (stops other pages and
        programs) for the API. The page itself is static and holds nothing secret, so a refresh may load it."""
        port = self.server.server_address[1]
        if self.headers.get("Host") not in ("127.0.0.1:%d" % port, "localhost:%d" % port):
            return False
        if urlparse(self.path).path == "/":
            return True
        return self.headers.get("X-Token") == self.server.token

    def do_GET(self):
        if not self.allowed():
            return self.send(403, {"error": "forbidden"})
        u = urlparse(self.path)
        if u.path == "/":
            with open(os.path.join(HERE, "page_gui.html"), "rb") as f:
                return self.send(200, f.read(), "text/html; charset=utf-8")
        route = GET_ROUTES.get(u.path)
        if not route:
            return self.send(404, {"error": "not found"})
        try:
            self.send(200, route(parse_qs(u.query)))
        except Exception as e:  # shown in the page, not a stack trace on the terminal
            self.send(500, {"error": "%s: %s" % (type(e).__name__, e)})

    def do_POST(self):
        if not self.allowed():
            return self.send(403, {"error": "forbidden"})
        path = urlparse(self.path).path
        if path == "/api/quit":
            self.send(200, {"ok": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        route = POST_ROUTES.get(path)
        size = int(self.headers.get("Content-Length") or 0)
        if not route or size > MAX_BODY:
            return self.send(404 if not route else 413, {"error": "not found or too large"})
        try:
            self.send(200, route(json.loads(self.rfile.read(size) or b"{}")))
        except Exception as e:
            self.send(500, {"error": "%s: %s" % (type(e).__name__, e)})


DEFAULT_PORT = 47931          # the same address each run, so the draft the page keeps in the browser is found again


def make_server(port=0):
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.token = token_urlsafe(24)
    return httpd


def make_default_server():
    try:
        return make_server(DEFAULT_PORT)
    except OSError:              # taken (another copy running): any free port
        return make_server(0)


def serve(open_browser=True):
    httpd = make_default_server()
    url = "http://127.0.0.1:%d/?t=%s" % (httpd.server_address[1], httpd.token)
    print("Page form running at %s\nPress Ctrl+C (or the Close button) to stop." % url)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    print("Stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(serve())
