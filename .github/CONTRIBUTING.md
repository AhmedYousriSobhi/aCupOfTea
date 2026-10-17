# Contributing

This guide covers the whole path for a new page: set up, write it, check it, preview it and send it. The repository layout is described in [SPEC.md](../SPEC.md).

## 1. Set up (once)

```bash
git clone https://github.com/AhmedYousriSobhi/aCupOfTea.git
cd aCupOfTea
pip install PyYAML==6.0.2     # the only requirement of the scripts (Python 3.12 in CI)
```

For each new topic, start from an up-to-date `dev` and give it its own branch (never work on `dev` or `main` directly):

```bash
git checkout dev && git pull
git checkout -b content/attention-in-transformers
```

## 2. Add the page

Every page is a markdown file in a folder. One command does the setup:

```bash
python3 .docs/tools/new_page.py
```

It asks for:

1. **Title.** It becomes the page heading and the file name (`Attention in Transformers` → `attention-in-transformers.md`).
2. **Summary**, optional. One line, shown in search results and in the folder index.
3. **Folder.** The closest existing folders are suggested first. It warns you if a similar page already exists, and it never creates a folder without asking.
4. **Type**: concept (explains an idea), guide (how to do something), reference (to look up), note, problem, project or experiment. Give one, or two comma separated with the main one first (`concept, guide`). The type most pages in that folder use is suggested. If none fits, type a new kind and you are asked to add it to `taxonomy.yaml` with a one-line definition (`--new-type KEY=DESCRIPTION` in a script).
5. **Domains**, up to three comma separated subjects that go together, such as `deep-learning` or `systems-and-hpc`. They put the page in Explore by subject. Each subject lists the ones it goes with (`related` in `taxonomy.yaml`); if two chosen subjects are not related you are told and asked whether to keep them together (`validate.py` warns the same way, and `page_doctor.py` offers to mark them related or drop one). A subject you add on the spot is marked related to the others on the page. The folder's usual subjects are suggested. A short form like `hpc` is matched to `systems-and-hpc`, and a subject that does not exist yet can be added (with a one-line description) after you confirm. A wrong answer is asked again instead of stopping the script.
6. **Tags**, optional. Pick from the tag list in `.docs/metadata/taxonomy.yaml` (Tab completes). A new tag is added only if you confirm, and if it looks like a known tag or a word of your title (`kubernates`, `k8s` for `kubernetes`) you are asked whether you meant that one.
7. **Level**, **prerequisites** and **related pages**, optional. `beginner` makes the page show under "Beginner friendly" in Start here. Prerequisites are ids of pages to read first, which builds a learning path; related pages show as "See also" under the title. Both take page ids (Tab completes).

You don't enter a reading time: the site works it out from the text (200 words a minute, code not counted) and shows it under the title, so it stays right when the page changes.

It then creates the page with a short outline to fill in, adds it to the folder's `README.md` index (any table whose rows start with a link, such as `Page | What it covers | Time`, or a list of links), and regenerates the site sidebar. For a folder it just created it also writes a `README.md` (a purpose line to fill in and the contents table) and adds the folder to the parent's `Directory` table.

To skip the questions, pass the answers as options:

```bash
python3 .docs/tools/new_page.py --title "Attention in Transformers" \
  --folder fields/deep-learning/concepts --tags transformers \
  --summary "How attention lets a model weigh every token." --level intermediate \
  --type concept --domains deep-learning --related sequence-models --yes
```

Add `--dry-run` to see the result without writing anything. Only Python 3 is needed.

## In your browser instead of the terminal

```bash
python3 .docs/tools/new_page.py --gui
```

It starts a small server on your own computer (127.0.0.1, a random port, protected by a token), prints the address and opens it. Three tabs: **New page** (the same questions as above as a form, with folder suggestions while you type the title, a warning about similar pages, tick boxes for kind and subjects, new subjects and tags added on the spot, Preview, Create), **Adopt a page** (the hand-written page flow below, with a filter box: type words of the path, title or a missing field, Enter picks the first match, the down arrow moves into the list) and **Fix problems** (the list of `page_doctor.py` below: open a problem in your editor, see the suggested fix as a diff, apply it). The form only fills in the options of `new_page.py` and runs it, so the rules are the same. The New page tab asks only for the essentials first (title, folder, summary, kind, subjects); tags, level and related pages are folded into "More options", a line at the bottom says what will be created, and your answers are kept as a draft in the browser, so closing the tab or stopping the server loses nothing (the address is the same each run: port 47931, unless it is taken). Stop it with Ctrl+C or the Close button. The same options work in a script: `--create-folder`, `--new-domain KEY=DESCRIPTION` and `--new-tag KEY=LABEL` confirm what the questions would ask.

## A page you wrote by hand

If you created the file yourself, add its front matter and index link without touching the text:

```bash
python3 .docs/tools/new_page.py --adopt fields/deep-learning/concepts/attention-in-transformers.md
```

The title comes from the page's `# ` heading and the folder from its path. It asks the same questions as a new page (summary, type, domains, tags, level, prerequisites, related), puts the front matter on top, adds the page to the folder `README.md` unless it is already listed, regenerates the sidebar and then shows the `--check` report. If the page already has front matter (for example only a `sidebar_label`), it keeps what is there and asks only for the missing fields; it says so when there is nothing to add. The page text is never changed. Add `--dry-run` to preview.

## Changing a page's metadata later

```bash
python3 .docs/tools/new_page.py --update fields/deep-learning/concepts/attention-in-transformers.md
```

It asks for the summary, kind, subjects, tags, level and relations with the current value as the default: Enter keeps it, `-` clears it. Options skip the questions (`--tags transformers,attention --level intermediate`). Only the changed fields are rewritten, other fields like `id` and `sidebar_label` and the page text stay as they are. `--dry-run` shows the change.

## Fixing what the checks report

`validate.py` and `check_links.py` print a list; `page_doctor.py` turns it into a to-do list for the pages you changed, with the page, the line and what to do:

```bash
python3 .docs/tools/page_doctor.py             # files changed since dev, interactive
python3 .docs/tools/page_doctor.py fields/devops   # one page or folder
```

Type a problem's number to open it in your editor at that line (`$VISUAL` or `$EDITOR`; VS Code, vim and nano get the line number), `f1` to apply the first suggested fix (it shows the change and asks first), `r` to check again, `q` to quit. Fixes it can make: a `../` link written root-absolute (or pointed at the file of that name), a misspelt or abbreviated tag or subject replaced (`kubernates`, `k8s` become `kubernetes`), a single-use tag that names a tool marked `kind: technology`. It also notices:

- **Stale generated indexes** (CI fails on those): the fix runs `generate_index.py` for you.
- **Pictures without a description**: with `--pictures` each one is listed at its line and the fix asks what it shows, then writes it into the brackets.
- **Swapped folder READMEs** (a folder's README that is about its subfolder and the other way round): the fix swaps the two files back.

Use `--list` to print only, `--errors-only` to leave out warnings and to-dos, `--apply-safe` to apply the fixes marked `[safe]`, and `--json` for scripts. "Changed files" means changed since the branch left `dev`, committed or not.

To catch errors before CI does, install a git hook that stops a push when the changed files have an error (skip it once with `git push --no-verify`):

```bash
python3 .docs/tools/page_doctor.py --install-hook      # --uninstall-hook removes it
```

It never overwrites a hook it did not make.

## When the page is written

```bash
python3 .docs/tools/new_page.py --check fields/deep-learning/concepts/attention-in-transformers.md
```

It shows the reading time readers will see, whether the page counts as a quick read (10 minutes or less), and what is still missing: outline notes from the template, empty sections, a summary, type, domains, tags or level, pictures described only as "image", and relative links that break on the site.

## Without the script

- Use a lowercase-kebab-case file name: `my-topic.md`.
- Start the page with one `# Heading`. The sidebar shows the text after the last hyphen, so `# Deep Learning - Attention` appears as **Attention**.
- Write links root-absolute: `/fields/deep-learning/concepts/basics.md`.
- Keep your own images in the repo: put them in an `images/` folder next to the page and link them relative to the page, `![caption](images/my-topic-01.png)`. Root-absolute paths do not work for images on the site. Pictures that belong to someone else stay links to their source.
- Add the page to its folder's `README.md` and run `cd .docs && ./gen_sidebar.sh`.

## 3. Check before you push

Run these from the repository root. CI runs the same checks and fails the pull request if one does not pass.

```bash
python3 .docs/tools/validate.py         # front matter and relations: must report 0 errors
python3 .docs/tools/check_links.py      # internal links and unsafe HTML: must report 0 broken links
python3 .docs/tools/generate_index.py   # rebuilds .docs/generated (Explore pages); commit the result
```

If you added, renamed or retitled a page by hand, also run `cd .docs && ./gen_sidebar.sh && ./gen_navbar.sh` and commit the result. `new_page.py` already does this for pages it creates. Never edit the generated files (`.docs/_sidebar.md`, `.docs/_navbar.md`, `.docs/generated/`) by hand.

## 4. Preview as readers will see it (optional)

```bash
python3 .docs/tools/stage_site.py --out _site     # the deployed version: reading time, Related strip, code pages
python3 -m http.server 8000 --directory _site     # then open http://localhost:8000
```

`_site/` is git-ignored. A plain `docsify serve` of the repository also works, but it does not show the reading time or the Related strip.

## All the scripts

| Script | Use it to |
|---|---|
| `new_page.py` | create a page, add it to its folder index and the sidebar; `--check PAGE` reviews a finished page |
| `validate.py` | check front matter, domains, tags and relations |
| `check_links.py` | find broken internal links, unsafe HTML and pictures without a description |
| `generate_index.py` | rebuild the Explore and Start here pages in `.docs/generated` |
| `stage_site.py` | build the deployed copy of the site locally, into `_site/` (git-ignored) |
| `update_recent.py` | refresh the "Recently added" list in the README; the maintainer runs it before a release |
| `check_pins.py` | compare the pinned CDN versions with npm and update their hashes (site maintenance) |

## Rules that save a review round

- Pages are content. Add or move things, but do not rewrite other people's pages in a structure PR.
- Put a page where it belongs; do not duplicate knowledge to make it visible twice, link to it instead. A project stays a project even when it uses a technology.
- Code files and notebooks keep their names and open as readable pages when linked root-absolute (`/folder/notebook.ipynb`).
- A new domain or tag goes into `.docs/metadata/taxonomy.yaml` before a page uses it.
- Raw `<script>`, `<iframe>` and `on...=` handlers are rejected by `check_links.py`.
- Do not commit generated or temporary files (`_site/`, caches, notes at the root).

## 5. Sending it

Commit on your branch and open a pull request into `dev`, one topic per pull request. The maintainer merges it and later releases `dev` to `main`, which redeploys the site. Never open a pull request directly to `main`.

By contributing, you agree that your writing is licensed under [CC BY 4.0](../LICENSE) and your code under the [MIT License](../LICENSE-CODE), as described in the README.
