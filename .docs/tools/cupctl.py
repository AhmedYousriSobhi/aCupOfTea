#!/usr/bin/env python3
"""cupctl: one entry point for every repository task, in the style of kubectl.

    cupctl <verb> <action> [args]

Run `cupctl` alone, or `cupctl <verb>`, to see what is available. Extra
arguments are passed on to the underlying script, so `cupctl page new --dry-run`
is `new_page.py --dry-run`. Each command prints the script it runs.

    page     new | gui | adopt PAGE | update PAGE | check PAGE | doctor
    check    all | fix | links | validate | pins
    nav      regen                       sidebar, navbar and .docs/generated
    site     build | serve [--port N]    preview the deployed site
    branch   new NAME                    cut a feature branch from dev
    release  prepare                     refresh "Recently added" before dev -> main
    hook     install | uninstall         pre-push doctor hook
    setup                                install the one dependency (PyYAML)

Put it on your PATH once:  alias cupctl='python3 /path/to/aCupOfTea/.docs/tools/cupctl.py'
Or run it in place:        python3 .docs/tools/cupctl.py page new
"""
import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(TOOLS))
PY = sys.executable or "python3"


def tool(name, *fixed):
    """A command that runs .docs/tools/<name> with fixed arguments, then the user's."""
    return lambda rest: [PY, os.path.join(TOOLS, name), *fixed, *rest]


def need_arg(what, rest, build):
    if not rest or rest[0].startswith("-"):
        sys.exit(f"cupctl: {what} is required (see `cupctl` for usage)")
    return build(rest)


def site_serve(rest):
    port = "8000"
    if "--port" in rest:
        i = rest.index("--port")
        port = rest[i + 1] if i + 1 < len(rest) else port
    return [PY, "-m", "http.server", port, "--directory", os.path.join(ROOT, "_site")]


def branch_new(rest):
    if not rest or rest[0].startswith("-"):
        sys.exit("cupctl: branch new needs a name, e.g. cupctl branch new contents/attention")
    return [["git", "fetch", "origin", "dev"], ["git", "switch", "-c", rest[0], "--no-track", "origin/dev"]]


def nav_regen(rest):
    docs = os.path.join(ROOT, ".docs")
    # the shell generators write into the current directory, so always run from .docs
    return [
        [PY, os.path.join(TOOLS, "generate_index.py")],
        {"cwd": docs, "cmd": ["./gen_sidebar.sh"]},
        {"cwd": docs, "cmd": ["./gen_navbar.sh"]},
    ]


def site_build(rest):
    return [PY, os.path.join(TOOLS, "stage_site.py"), "--out", os.path.join(ROOT, "_site"), *rest]


def setup(rest):
    return [PY, "-m", "pip", "install", "PyYAML==6.0.2", *rest]


def hook(flag):
    return lambda rest: [PY, os.path.join(TOOLS, "page_doctor.py"), flag, *rest]


# verb -> (summary, {action: (summary, builder)})
COMMANDS = {
    "page": ("create and maintain pages", {
        "new": ("ask a few questions and create a page", tool("new_page.py")),
        "gui": ("the same, as a form in your browser", tool("new_page.py", "--gui")),
        "adopt": ("add front matter and index link to a hand-written page", lambda r: need_arg("PAGE", r, tool("new_page.py", "--adopt"))),
        "update": ("change the metadata of a page", lambda r: need_arg("PAGE", r, tool("new_page.py", "--update"))),
        "check": ("reading time and what is still missing", lambda r: need_arg("PAGE", r, tool("new_page.py", "--check"))),
        "doctor": ("to-do list for the pages you changed", tool("page_doctor.py")),
    }),
    "check": ("validate the repository", {
        "all": ("run the whole suite, change nothing (what CI does)", tool("check_all.py")),
        "fix": ("run the suite and keep the regenerated files", tool("check_all.py", "--fix")),
        "links": ("internal links and unsafe HTML", tool("check_links.py")),
        "validate": ("front matter and taxonomy", tool("validate.py")),
        "pins": ("pinned CDN versions against npm", tool("check_pins.py")),
    }),
    "nav": ("sidebar and navbar", {
        "regen": ("regenerate sidebar, navbar and .docs/generated", nav_regen),
    }),
    "site": ("preview the deployed site", {
        "build": ("build the staged copy into _site/", site_build),
        "serve": ("serve _site/ on http://localhost:8000 (--port N)", site_serve),
    }),
    "branch": ("git branches", {
        "new": ("cut NAME from origin/dev", branch_new),
    }),
    "release": ("dev -> main", {
        "prepare": ("refresh the Recently added list, then commit README.md on dev", tool("update_recent.py")),
    }),
    "hook": ("git hooks", {
        "install": ("refuse a push with errors in changed pages", hook("--install-hook")),
        "uninstall": ("remove that hook", hook("--uninstall-hook")),
    }),
    "setup": ("install the one dependency", {None: ("pip install PyYAML", setup)}),
}


def usage(verb=None):
    out = ["usage: cupctl <verb> <action> [args]", ""]
    for v, (vs, actions) in COMMANDS.items():
        if verb and v != verb:
            continue
        if None in actions:
            out.append(f"  {v:<8} {vs}")
            continue
        out.append(f"  {v:<8} {vs}")
        for a, (s, _) in actions.items():
            out.append(f"      {v} {a:<9} {s}")
    return "\n".join(out)


def run(step):
    cwd = ROOT
    if isinstance(step, dict):
        cwd, step = step["cwd"], step["cmd"]
    print("$", " ".join(os.path.relpath(c, ROOT) if os.path.isabs(c) and c.startswith(ROOT) else c for c in step), flush=True)
    return subprocess.call(step, cwd=cwd)


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(usage())
        return 0
    verb = argv[0]
    if verb not in COMMANDS:
        print(f"cupctl: unknown verb '{verb}'\n\n{usage()}", file=sys.stderr)
        return 2
    _, actions = COMMANDS[verb]
    if None in actions:
        action, rest = None, argv[1:]
    elif len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(usage(verb))
        return 0 if len(argv) > 1 else 2
    elif argv[1] not in actions:
        print(f"cupctl: unknown action '{verb} {argv[1]}'\n\n{usage(verb)}", file=sys.stderr)
        return 2
    else:
        action, rest = argv[1], argv[2:]
    plan = actions[action][1](rest)
    steps = plan if plan and isinstance(plan[0], (list, dict)) else [plan]
    for step in steps:
        code = run(step)
        if code:
            return code
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
