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
4. **Type**: concept (explains an idea), guide (how to do something), reference (to look up), note, problem, project or experiment. Give one, or two comma separated with the main one first (`concept, guide`). The type most pages in that folder use is suggested.
5. **Domains**, one or two comma separated subjects such as `deep-learning` or `systems-and-hpc`. They put the page in Explore by subject. The folder's usual subjects are suggested. A short form like `hpc` is matched to `systems-and-hpc`, and a subject that does not exist yet can be added (with a one-line description) after you confirm. A wrong answer is asked again instead of stopping the script.
6. **Tags**, optional. Pick from the tag list in `.docs/metadata/taxonomy.yaml` (Tab completes). A new tag is added only if you confirm.
7. **Level**, **prerequisites** and **related pages**, optional. `beginner` makes the page show under "Beginner friendly" in Start here. Prerequisites are ids of pages to read first, which builds a learning path; related pages show as "See also" under the title. Both take page ids (Tab completes).

You don't enter a reading time: the site works it out from the text (200 words a minute, code not counted) and shows it under the title, so it stays right when the page changes.

It then creates the page with a short outline to fill in, adds it to the folder's `README.md` index (a `File | Description` table, or a list of links), and regenerates the site sidebar.

To skip the questions, pass the answers as options:

```bash
python3 .docs/tools/new_page.py --title "Attention in Transformers" \
  --folder fields/deep-learning/concepts --tags transformers \
  --summary "How attention lets a model weigh every token." --level intermediate \
  --type concept --domains deep-learning --related sequence-models --yes
```

Add `--dry-run` to see the result without writing anything. Only Python 3 is needed.

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
