#!/usr/bin/env python3
"""Readable site pages for code files and notebooks (used by stage_site.py).

Docsify adds ".md" to every link, so a link to `name.py` or `name.ipynb` asks
for `name.py.md`. In the staged copy this writes exactly that file:

  * a script: its source, highlighted;
  * a notebook: markdown cells as text, code cells highlighted, text and table
    outputs, and output pictures saved next to it as files
    (`name.ipynb-files/out-N.png`).

Each page starts with links to the file on GitHub (and Colab for notebooks).
The pages are in no menu and no search index; sources are never modified.
"""
import base64
import json
import os
import re

REPO = "AhmedYousriSobhi/aCupOfTea"
BRANCH = "main"  # the site is built from main
LANGS = {".py": "python", ".sh": "bash", ".r": "r", ".sql": "sql", ".js": "javascript",
         ".c": "c", ".cpp": "cpp", ".java": "java", ".go": "go", ".ts": "typescript",
         ".yaml": "yaml", ".yml": "yaml", ".nhc": "bash"}
MAX_OUTPUT_LINES = 60
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[@-_]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")  # left after ANSI codes are removed
STYLE_RE = re.compile(r"<style[\s\S]*?</style>", re.I)
UNSAFE_HTML_RE = re.compile(r"<\s*(script|iframe|object|embed)\b|<[a-z][^>]*\son\w+\s*=|javascript:", re.I)
IMAGE_TYPES = {"image/png": "png", "image/jpeg": "jpg"}


def fence(code, lang=""):
    """A fenced block that no backtick run inside the code can close."""
    longest = max((len(m) for m in re.findall(r"`+", code)), default=0)
    ticks = "`" * max(3, longest + 1)
    return f"{ticks}{lang}\n{code.rstrip()}\n{ticks}"


def text_of(src):
    return "".join(src) if isinstance(src, list) else (src or "")


def header(path, notebook):
    view = f"https://github.com/{REPO}/blob/{BRANCH}/{path}"
    raw = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}"
    links = [f"[View on GitHub]({view})", f"[Raw file]({raw})"]
    if notebook:
        links.append(f"[Open in Colab](https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{path})")
    kind = "Notebook" if notebook else "Code file"
    return (f"# {os.path.basename(path)}\n\n"
            f'<div class="code-file">\n\n{kind} from the repository  ·  {"  ·  ".join(links)}\n\n</div>\n')


def clip(text):
    lines = ANSI_RE.sub("", text).rstrip("\n").split("\n")
    if len(lines) > MAX_OUTPUT_LINES:
        more = len(lines) - MAX_OUTPUT_LINES
        lines = lines[:MAX_OUTPUT_LINES] + [f"... {more} more lines (the full output is in the notebook on GitHub)"]
    return "\n".join(lines)


def render_outputs(outputs, files_dir, files_rel, counter):
    parts = []
    for out in outputs:
        kind = out.get("output_type")
        if kind == "stream":
            parts.append(fence(clip(text_of(out.get("text"))), "output"))
        elif kind == "error":
            parts.append(fence(clip("\n".join(out.get("traceback") or [out.get("ename", "Error")])), "output"))
        elif kind in ("execute_result", "display_data"):
            data = out.get("data", {})
            img = next((m for m in IMAGE_TYPES if m in data), None)
            # a widget's saved HTML only says "rerun in Jupyter"; its plain text says more
            html = "" if "application/vnd.jupyter.widget-view+json" in data else text_of(data.get("text/html"))
            if img:
                counter[0] += 1
                name = f"out-{counter[0]}.{IMAGE_TYPES[img]}"
                os.makedirs(files_dir, exist_ok=True)
                with open(os.path.join(files_dir, name), "wb") as f:
                    f.write(base64.b64decode(text_of(data[img])))
                parts.append(f"![output {counter[0]}]({files_rel}/{name})")
            elif html and not UNSAFE_HTML_RE.search(html):
                # tables (pandas) read better as HTML; drop their inline styles
                parts.append(f'<div class="nb-output">\n\n{STYLE_RE.sub("", html).strip()}\n\n</div>')
            elif "text/plain" in data:
                parts.append(fence(clip(text_of(data["text/plain"])), "output"))
    return parts


def notebook_page(out_root, path):
    full = os.path.join(out_root, path)
    page = [header(path, True)]
    try:
        with open(full, encoding="utf-8") as f:
            nb = json.load(f)
    except (ValueError, UnicodeDecodeError):
        return "\n".join(page + ["This notebook file is empty or not valid JSON in the repository."]) + "\n"
    meta = nb.get("metadata", {})
    lang = (meta.get("kernelspec", {}).get("language") or meta.get("language_info", {}).get("name") or "python")
    files_rel = os.path.basename(path) + "-files"
    files_dir = os.path.join(os.path.dirname(full), files_rel)
    counter = [0]
    for cell in nb.get("cells", []):
        src = text_of(cell.get("source"))
        if cell.get("cell_type") == "markdown":
            # a cell with script-like HTML is shown as text, never run on the site
            page.append(fence(src, "markdown") if UNSAFE_HTML_RE.search(src) else src)
        elif cell.get("cell_type") == "code":
            if src.strip():
                page.append(fence(src, lang))
            page += render_outputs(cell.get("outputs", []), files_dir, files_rel, counter)
        elif src.strip():
            page.append(fence(src))
    return "\n\n".join(page) + "\n"


def script_page(out_root, path, lang):
    with open(os.path.join(out_root, path), encoding="utf-8", errors="replace") as f:
        src = f.read()
    return header(path, False) + "\n" + fence(src, lang) + "\n"


def write_code_pages(out_root, skip_dirs):
    """Writes name.ext.md next to every code file and notebook; returns how many."""
    count = 0
    for dirpath, dirnames, filenames in os.walk(out_root):
        rel_dir = os.path.relpath(dirpath, out_root).replace(os.sep, "/")
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"
                       and (d if rel_dir == "." else f"{rel_dir}/{d}") not in skip_dirs]
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext != ".ipynb" and ext not in LANGS:
                continue
            path = name if rel_dir == "." else f"{rel_dir}/{name}"
            text = notebook_page(out_root, path) if ext == ".ipynb" else script_page(out_root, path, LANGS[ext])
            # terminal colour codes and other control characters never reach the page
            text = CONTROL_RE.sub("", ANSI_RE.sub("", text))
            with open(os.path.join(out_root, path + ".md"), "w", encoding="utf-8") as f:
                f.write(text)
            count += 1
    return count
