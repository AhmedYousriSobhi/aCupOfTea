#!/usr/bin/env python3
"""Generate .docs/_navbar.md: Home, a Categories dropdown of the top-level folders, External links.

Never hand-edit the output. `.docs/gen_navbar.sh` runs this script."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pagemodel import title_case_words  # noqa: E402

DOCS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(DOCS)
OUTPUT = os.path.join(DOCS, "_navbar.md")
GITHUB_REPO = "AhmedYousriSobhi/aCupOfTea"
GITHUB_PROFILE = "https://github.com/AhmedYousriSobhi"
LINKEDIN_PROFILE = "https://www.linkedin.com/in/ahmedyousrisobhi/"


def build(root=ROOT):
    out = ["* [🏠 Home](README.md)", "", "* 📂 Categories"]
    with os.scandir(root) as it:
        dirs = sorted((e.name for e in it
                       if e.is_dir(follow_symlinks=False) and not e.name.startswith(".") and e.name != "_site"),
                      key=os.fsencode)
    for name in dirs:
        has_readme = os.path.isfile(os.path.join(root, name, "README.md"))
        out.append(f"  * [{title_case_words(name)}]({name}/README.md)" if has_readme
                   else f"  * [{title_case_words(name)}]({name}/)")
    out += ["", "* 🔗 External",
            f"  * [GitHub](https://github.com/{GITHUB_REPO})",
            f"  * [Profile]({GITHUB_PROFILE})",
            f"  * [LinkedIn]({LINKEDIN_PROFILE})"]
    return "\n".join(out) + "\n"


def main():
    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(build())
    print("Done! _navbar.md generated.")


if __name__ == "__main__":
    main()
