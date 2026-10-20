# Contributing ☕

Got something worth a coffee break? Adding a page takes about five minutes, and you can do it from the **terminal** or from a **browser form**. Both ask the same few questions and follow the same rules. (How the repository is laid out: [SPEC.md](/SPEC.md).)

**The whole trip:** set up once → make a branch → write the page → let the checker nag you → open a pull request.

## 1. Set up (once)

```bash
git clone https://github.com/AhmedYousriSobhi/aCupOfTea.git
cd aCupOfTea
pip install PyYAML==6.0.2     # the only thing the scripts need (plus Python 3)
```

## 2. One topic, one branch

Always start from an up-to-date `dev` (never work on `dev` or `main` directly):

```bash
git checkout dev && git pull
git checkout -b content/attention-in-transformers
```

## 3. Write the page: pick your path

### 🖥️ I live in the terminal

```bash
python3 .docs/tools/new_page.py
```

It asks, you answer. **Enter accepts the suggestion** in brackets, a typo is asked again instead of crashing, and nothing is written until you have answered everything. Add `--dry-run` to only look.

![The terminal asking for title, summary, folder, kind, subjects, tags and level, then printing the page it would create](/.github/images/terminal-new-page.png)
*A real run with `--dry-run`: what it asks, then what it would write.*

You will be asked for, in this order:

| Question | In plain words |
|---|---|
| **Title** | Becomes the heading and the file name (`Attention in Transformers` → `attention-in-transformers.md`). |
| **Summary** | One line, optional. Shown in search results. |
| **Folder** | Closest existing folders are suggested. It never creates one without asking. |
| **Kind** | `concept`, `guide`, `reference`, `note`, `problem`, `project` or `experiment`. None fits? Type a new one and add its definition. |
| **Subjects** | Up to three that go together, like `deep-learning`. They put the page in Explore. Pairs that do not go together get a warning. |
| **Tags** | Optional, from the list (Tab completes). A new tag that looks like a typo of a known one (`k8s`, `kubernates`) is caught. |
| **Level, prerequisites, related** | Optional. `beginner` shows the page under "Beginner friendly". |

No reading time to enter: the site counts it from your text.

Want to skip the questions? Pass the answers:

```bash
python3 .docs/tools/new_page.py --title "Attention in Transformers" \
  --folder fields/deep-learning/concepts --type concept --domains deep-learning \
  --tags transformers --summary "How attention lets a model weigh every token." --yes
```

### 🖱️ I prefer buttons

```bash
python3 .docs/tools/new_page.py --gui
```

A small form opens in your browser (it runs only on your own computer). Fill the five essentials; the cup fills up as you go.

![The New page tab: title, folder, summary and kind filled in, the cup progress bar full, and a bar at the bottom with Preview and Create page](/.github/images/gui-new-page-top.png)

Scroll down for subjects. A little map shows whether the subjects you picked go together, and a card shows how the page will look in search:

![The subject chips with two selected, a map joining them, the how-it-will-look card and the Create page button](/.github/images/gui-new-page-bottom.png)

Press **Preview** to see what would be written, then **Create page**. Closed the tab by accident? Your answers are kept as a draft. The other tabs (Adopt, Edit, Add pictures, Fix problems) are covered below.

## 4. Fill in the page

Open the new file and replace the comments in the outline with your own words. Your own images go in an `images/` folder next to the page and are linked relative to it: `![what it shows](images/my-topic-01.png)` (the **Add pictures** tab does this for you).

## 5. Let the checker nag you

```bash
python3 .docs/tools/page_doctor.py
```

It checks the pages you changed and gives you a to-do list: which file, which line, what to do. Type a number to open the problem in your editor, `f1` to apply the suggested fix (it shows the change and asks first).

![The doctor listing a wrong tag, a link that breaks on the site, a missing picture and a picture without a description, each with the file and line](/.github/images/terminal-doctor.png)

Prefer clicking? The **Fix problems** tab shows the same list with **Open in editor** and **Fix** buttons:

![The Fix problems tab listing the same problems as cards with Open in editor and Fix buttons](/.github/images/gui-fix-problems.png)

CI runs the same checks. To run them all by hand, and update the sidebar, navbar and `.docs/generated` in one go, run this and commit what it changes:

```bash
python3 .docs/tools/check_all.py --fix
```

It runs `validate.py`, `check_links.py`, the generators and every `test_*.py`; without `--fix` it only reports a stale generated file, which is what CI does.

To put a page at a given place in its folder (a series read in order), add `order: 1`, `order: 2`, ... to the front matter of its pages; the sidebar, Previous/Next and "Read next" follow that order. Pages without `order` follow the order of the folder `README.md` table.

## 6. Preview it

Look at the deployed version of your page in a browser before you push.

1. Build the site and serve it:

   ```bash
   python3 .docs/tools/stage_site.py --out _site
   python3 -m http.server 8000 --directory _site
   ```

2. Open http://localhost:8000 and check:
   - your page is in the left menu, in the order of its folder `README.md` table;
   - its reading time, links and images show up and work;
   - it reads well in a narrow window (phone width).
3. Stop the server with Ctrl+C. `_site/` is git-ignored.

To see the reading time and what is still missing without a browser, run `python3 .docs/tools/new_page.py --check PAGE`.

## 7. Send it

Commit, push, and open a pull request **into `dev`** (never `main`), one topic per pull request. The maintainer merges it and later releases `dev` to `main`, which updates the site.

By contributing, you agree that your writing is licensed under [CC BY 4.0](/LICENSE) and your code under the [MIT License](/LICENSE-CODE).

---

## More, only when you need it

<details>
<summary><b>I already wrote the page by hand</b></summary>

```bash
python3 .docs/tools/new_page.py --adopt fields/deep-learning/concepts/attention-in-transformers.md
```

Adds the front matter and the folder index link without touching your text. It keeps any front matter that is already there and asks only for what is missing. In the form: the **Adopt a page** tab (type words of the path or title to filter the list).
</details>

<details>
<summary><b>Change the summary, kind, subjects, tags or level later</b></summary>

```bash
python3 .docs/tools/new_page.py --update fields/deep-learning/concepts/attention-in-transformers.md
```

Enter keeps the current value, `-` clears it. Only what you change is rewritten. In the form: the **Edit a page** tab.
</details>

<details>
<summary><b>No scripts at all</b></summary>

- A lowercase-kebab-case file name: `my-topic.md`, starting with one `# Heading`.
- Root-absolute links: `/fields/deep-learning/concepts/basics.md` (relative `../` links break on the site; images are the exception, see above).
- Add the page to its folder's `README.md` table, then `cd .docs && ./gen_sidebar.sh && ./gen_navbar.sh`.
- Never edit the generated files (`.docs/_sidebar.md`, `.docs/_navbar.md`, `.docs/generated/`) by hand.
</details>

<details>
<summary><b>Stop a broken push before it leaves your machine</b></summary>

```bash
python3 .docs/tools/page_doctor.py --install-hook      # --uninstall-hook removes it
```

A git hook that refuses a push when the changed files have an error (skip once with `git push --no-verify`).
</details>

<details>
<summary><b>Keep the menu and indexes up to date on every commit</b></summary>

```bash
git config core.hooksPath .docs/hooks
```

A `pre-commit` hook regenerates the sidebar, navbar and `.docs/generated` and adds them to the commit (skip once with `git commit --no-verify`).
</details>

<details>
<summary><b>All the scripts</b></summary>

| Script | Use it to |
|---|---|
| `new_page.py` | create a page (`--gui` for the form), `--adopt`, `--update`, `--check` |
| `page_doctor.py` | the to-do list of fixes for changed pages, and the optional pre-push hook |
| `page_gui.py` | the browser form behind `--gui` |
| `check_all.py` | the whole suite: validate, links, generators up to date, tests (`--fix` applies them) |
| `validate.py` | check front matter, subjects, tags and relations |
| `check_links.py` | broken links, unsafe HTML, pictures without a description |
| `generate_index.py` | rebuild the Explore and Start here pages in `.docs/generated` |
| `stage_site.py` | build the deployed copy of the site into `_site/` |
| `update_recent.py` | the maintainer runs it before a release |
| `check_pins.py` | site maintenance: compare pinned CDN versions with npm |
| `test_*.py` | tests of the tools (CI runs them) |
</details>

<details>
<summary><b>Rules that save a review round</b></summary>

- Pages are content: add or move things, but do not rewrite other people's pages in a structure PR.
- Put a page where it belongs; link instead of duplicating. A project stays a project even when it uses a technology.
- A new subject or tag goes into `.docs/metadata/taxonomy.yaml` before a page uses it (the tools offer to add it).
- Raw `<script>`, `<iframe>` and `on...=` handlers are rejected by `check_links.py`.
- Do not commit generated or temporary files (`_site/`, caches, notes at the root).
</details>
