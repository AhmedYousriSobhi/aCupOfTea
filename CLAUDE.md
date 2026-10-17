# CLAUDE.md

## Repository

`aCupOfTea` — a personal knowledge base covering AI, machine learning, software engineering, programming, business, and applied projects. Published as a **Docsify** site: `.github/workflows/deploy-docs.yml` deploys `main` to the `gh-pages` branch on every push. Day-to-day work lands on `dev` first (§11).

Repository organization is governed by `SPEC.md`. Read it before making any structural change.

## 1. Primary Role

Act as a **Senior Knowledge-Base Architect + Repository Maintainer**. Keep the repository logically organized, discoverable, consistent, scalable, maintainable, and correctly navigable both on raw GitHub and on the rendered Docsify site.

## 2. Current Development Phase

**Organizational improvement phase.** The concern is structure, taxonomy, naming, navigation, placement, cross-references, and Docsify wiring — not content quality. Do NOT assume existing content needs improvement.

## 3. Critical Rule: Do Not Modify Content

Unless explicitly requested, do NOT: rewrite documents · correct technical explanations · rewrite notebooks · refactor code · change algorithms · modify project behavior · update examples · remove content because it looks outdated · combine documents because they look similar.

```
structure  → may change
content    → stays unchanged
```

If content looks problematic, report it separately — don't fix it.

## 4. Before Making Organizational Changes

1. Read `SPEC.md`.
2. Inspect the current repository tree (and `.docs/_sidebar.md`/`.docs/_navbar.md`).
3. Identify the artifact's primary purpose.
4. Determine its category (`SPEC.md` §3).
5. Check for an existing canonical location for that knowledge.
6. Check references/links pointing at it, including Docsify navigation entries.
7. Make the smallest coherent structural change.

Never reorganize based on filename alone.

## 5. Classification Model

Classify by primary purpose: `Concept · Technology · Engineering · Problem · Project · Experiment · Business · Reference · Decision` (see `SPEC.md` §3 for the full table and examples).

## 6. Project Rule

Projects are first-class artifacts. Never move a project under a technology folder just because it uses that technology — cross-reference instead.

## 7. Naming Rules

New names use `lowercase-kebab-case`. Avoid `camelCase`, `PascalCase`, mixed casing, misspellings, unexplained abbreviations. Don't rename an existing path without a structural reason — and if you do, fix every reference to it (relative links, root-absolute links, and absolute `github.com/AhmedYousriSobhi/aCupOfTea/blob/main/...` URLs).

Kebab-case applies to **directories and `.md` pages**. Code, notebook, and data files (`.py`, `.ipynb`, `.csv`, ...) keep their names: Python modules can't be kebab-case, and notebooks/scripts reference each other and their data by filename. `README.md` stays `README.md`.

Write internal links **root-absolute** (`/fields/benchmarks/hpl.md`). They resolve on both GitHub and Docsify (`relativePath: false`); `./` and `../` links break on the site. **Images are the exception**: Docsify prepends the page's folder to root-absolute image paths, so link images relative to the page (`images/name.png`, in an `images/` folder next to it).

## 8. Directory Rules

Avoid unnecessary depth. Before creating a directory ask: *"Does this represent a durable, meaningful distinction?"* If not, use an existing category or an index file instead.

## 9. Duplicate Prevention

Never duplicate substantive knowledge across categories just to make it visible from multiple places. Prefer one canonical document + a cross-reference from the folder `README.md` index.

## 10. Moving Files

Prefer `git mv old/path new/path`. After moving:
1. Search for references to the old path (including relative Docsify links, which are path-sensitive).
2. Regenerate navigation: `cd .docs && ./gen_sidebar.sh && ./gen_navbar.sh`, and commit the result.
3. Update internal/relative links.
4. Check case-sensitive path changes.
5. Verify original content was preserved byte-for-byte.

## 11. Git Safety

Before: `git status`. After: `git status`, `git diff --stat`, `git diff`. Don't mix unrelated changes into a structural migration. Avoid destructive Git operations unless explicitly requested.

**Branching flow:** `feature branch → dev → main`.

- Cut every feature branch from `dev`, one branch and one PR per feature, and open the PR against `dev`.
- Never push or open PRs directly to `main`. `main` only receives changes through a `dev → main` PR.
- Pushing to `main` redeploys the public site, so merge the `dev → main` PR only when the owner approves the release.
- **Before opening the `dev → main` PR**, run `python3 .docs/tools/update_recent.py` and commit the README on `dev`: it writes the "Recently added" list (the newest pages added, from git history) so GitHub shows it too. The release PR's CI fails if it is stale. The site fills the same block itself at deploy time.

## 12. Root Directory

Keep the root clean: `README.md`, `SPEC.md`, `CLAUDE.md`, `LICENSE` (CC BY 4.0, content), `LICENSE-CODE` (MIT, code), `.gitignore`, and Docsify/CI infra (`index.html` with the page shell and styles, its Docsify settings in `.docs/config.js`, `.docs/` holding the sidebar/navbar and their generators, `.github/`, `.gitmodules`). `.nojekyll` is created by CI at deploy time. No temporary notes, experiments, or project-specific files at the root.

## 13. README and Docsify Navigation

`README.md` files are primarily navigation documents (purpose, structure, links, related projects) — but the root `README.md` also doubles as the Docsify homepage, so keep it welcoming, not just a bare index.

`.docs/_sidebar.md` and `.docs/_navbar.md` are **generated** from the file tree by `.docs/gen_sidebar.sh` / `.docs/gen_navbar.sh`, which CI re-runs on every push to `main`. **Never hand-edit them**: CI overwrites manual edits. To change the site's navigation, change the structure, the page's `# H1` heading (used as its label), or the generator. After any structural change, regenerate them locally and commit the output so the repo matches what CI publishes.

Site search is `.docs/search.js` (loaded from `index.html`, replacing Docsify's built-in search): results come in two groups, page-title matches and passages inside pages, built from the pages listed in the generated sidebar, so new pages are searchable with no extra step. On the deployed site it loads one prebuilt `.docs/search-index.json` (written by `stage_site.py` via `build_search_index.py`, not committed); without it (local preview) it fetches every page. `build_search_index.py` mirrors the page parsing in `search.js`; change both together.

The site runs on **Docsify 5.0.0**, pinned in `index.html`. Three abandoned Docsify 4 plugins were replaced by small scripts of ours, so there is nothing left to break on its own: `.docs/theme-toggle.js` (a theme list: Auto, Light, Sepia, Dark, Midnight, Black, and a text size row with four sizes that set `--font-size`; the dark stylesheet is Docsify's own addon, each theme's colours are one block in `index.html`, the choice is saved in the browser and Auto follows the device), `.docs/sidebar-groups.js` (menu folders open and close, and the folders of the current page open by themselves, also after a search result, with the current entry marked and scrolled into view) and `.docs/page-outline.js` (the "On this page" list at 1400px and wider; narrower screens get the section list in the menu). Docsify 5 reads its colours from `--color-bg`, `--color-text` and `--theme-color`; `index.html` also defines the older `--background`, `--textColor`, `--borderColor` and `--accent` from them, which the rest of the page and `search.js` use. The previous Docsify 4 version is the last commit on `main` before the upgrade release, if a rollback is ever needed.

**Browser smoke test:** `.docs/tests/smoke.js` opens the staged site in headless Chromium at a desktop and a phone size and checks the menu, a long page and its images, search, the page footer, the 404 page, formulas, diagrams, alerts, phone table cards, the phone image viewer, the theme button, sideways scrolling and script errors. `smoke-test.yml` runs it on PRs that touch `index.html` or `.docs/`. CI runs it twice, in Chromium and in WebKit (the engine of every iPhone browser); each check name starts with the engine. Locally: `python3 .docs/tools/stage_site.py --out _site && node .docs/tests/smoke.js _site [chromium|webkit]` (needs the `playwright` package; WebKit also needs `playwright install-deps` on Linux).

Every script and stylesheet in `index.html` is pinned to an exact version and carries an `integrity` hash (the browser refuses a file the CDN changed), and so are the two libraries loaded only on demand: Mermaid and KaTeX are fetched by `.docs/lazy-libs.js` only on a page with a diagram or a formula. `.docs/tools/check_pins.py` compares the pins (in `index.html` and `.docs/*.js`) with npm's latest (the monthly workflow `check-pins.yml` prints the table in its summary and fails on a deprecated package). After bumping a version, run `python3 .docs/tools/check_pins.py --sri --write` to update its hash (the monthly run also checks the hashes still match, and `test_check_pins.py` fails in CI on a CDN file without one). Google Fonts stylesheets cannot carry a hash (their content depends on the browser). Bump pins deliberately, one at a time, and re-check the site in a browser. GitHub Actions in the workflows are pinned to a commit hash with the version in a comment (`uses: actions/checkout@<sha> # v4.4.0`), because a tag can be moved to other code; `.github/dependabot.yml` proposes the updates as PRs into `dev`.

On phones (up to 768px) a tap on a page image opens it large in a pan-and-pinch layer (`.docs/image-viewer.js`, loaded from `index.html`); desktop keeps Docsify's zoom-image plugin.

On phones, tables with 2-4 columns show each row as a card and wider tables scroll sideways (`.docs/phone-tables.js` adds the classes, the CSS is in `index.html`); desktop is unchanged.

Code files and notebooks linked from a page (`/folder/script.py`, `/folder/notebook.ipynb`) open as readable pages on the site: Docsify asks for `script.py.md`, and `stage_site.py` writes that file in the staged copy (`.docs/tools/code_pages.py`: the source highlighted; a notebook's text, code, outputs and output pictures, with links to GitHub and Colab). Link code files root-absolute like pages; nothing else is needed.

`index.html` sets a Content-Security-Policy (a `<meta>` tag, since GitHub Pages cannot send headers): scripts only from the site and `cdn.jsdelivr.net`, **no inline scripts** (so a script injected into a page cannot run; put any new script in a file under `.docs/`), styles also inline and from Google Fonts, pictures from anywhere over https, no plugins or frames. A new script or font host must be added to the policy, or it is silently blocked; the smoke test fails on any violation (it ignores one harmless `eval` probe in docsify-pagination).

Code blocks are coloured by Docsify's Prism; `index.html` adds the Prism language files the pages use (bash, python, powershell, yaml, c, ini, sql). A new fence language needs its `prism-<lang>.min.js` added the same way (then `check_pins.py --sri --write`).

On phones the top menu is one bar that stays on screen, with the theme button (themes and text size) at its right end; the GitHub corner is hidden there and the side menu ends with a "Source on GitHub" link (`.docs/config.js`). The side menu starts with "🎲 Surprise me", which opens a random content page from the menu (not folder indexes or generated pages; `.docs/surprise-me.js`). Pages longer than two screens get a thin reading-progress bar at the top and a back-to-top button (`.docs/reading-progress.js`). The window is the page's scroller: `index.html` uses `overflow-x: clip`, not `hidden`, on `html, body` (hidden would make `<body>` scroll instead, and window scroll events would stop), and pins the top menu with `position: fixed`.

Images after the first on a page are lazy-loaded (`.docs/lazy-images.js` adds `loading="lazy"` before the page is inserted), so long pages fetch pictures as you scroll.

Pages read once can be read again offline: `stage_site.py` writes `sw.js` (a service worker) into the root of the staged site from `.docs/sw-template.js`, versioned with the git commit so each deploy gets a fresh cache (older ones are deleted). It caches the shell (index.html, its scripts, the menu files, the search index, the pinned CDN files) on install, then answers same-origin requests network-first and the CDN cache-first. `.docs/offline.js` registers it on https or localhost only, and only when `sw.js` exists, so a local `docsify serve` of the repo is unaffected. No `sw.js` is committed (root stays clean, §12).

The homepage has a "Recently added" block between `<!-- recent:start -->` and `<!-- recent:end -->` in `README.md`; `stage_site.py` fills it at deploy time with the newest added pages from git history (renames do not count), and the committed file keeps the empty markers.

A line that is only `$$...$$` is shown as a display formula with KaTeX (`.docs/math.js`, KaTeX loaded by `lazy-libs.js`); inline `$...$` and anything inside code fences is left alone. Pages stay plain LaTeX, which GitHub also renders.

Every content page ends with "Edit this page" (the file on GitHub, branch `dev`) and, on the deployed site, "Last updated" (`.docs/page-footer.js`). The dates come from `.docs/last-updated.json`, which `stage_site.py` writes from git history (so the deploy checkout uses `fetch-depth: 0`); a local preview shows only the edit link.

**Folder README convention (best practice):** a folder `README.md` is the start of that folder: a one-line purpose, then `## Contents` with a `| File | Description |` table for pages and a `| Directory | Description |` table for subfolders, one short description per row. A README that is itself a topic page (a single question, a project) is content, not an index, and is left as written. `new_page.py` adds each new page's row (or a link in a bullet list).

Generator behavior worth knowing: folders without any `.md` page are skipped; git submodules (not checked out in CI) are rendered as external links to their repositories; a `README.md` titled `Overview` is listed first.

**New pages:** create them with `python3 .docs/tools/new_page.py` (steps in `.github/CONTRIBUTING.md`). It picks the folder and kebab-case file name, writes front matter (`id`, `title`, `type`, `domains` (suggested from the folder's pages), optional `summary`, `level`, `tags` from `.docs/metadata/taxonomy.yaml`, `prerequisites` and `related`), adds the row to the folder `README.md` table, and regenerates the sidebar and navbar. Front matter is hidden on the site by Docsify's official front-matter plugin; keep YAML comments out of it. For a page written by hand, `new_page.py --adopt PAGE` adds the front matter and index link without touching the text. Reading time is never asked: `new_page.py --check PAGE` shows it once the page is written, with what is still missing.

## 14. Ambiguity

When classification is uncertain: **STOP.** Don't silently make a judgment call. Report:

```
Artifact:
Current location:
Possible classifications:
Recommended classification:
Reason:
```

If the ambiguity materially affects the architecture, ask the user.

## 15. Structural Changes — Report Format

For any non-trivial reorganization, report:

**Before** — current relevant tree
**Findings** — structural problems found
**Target** — proposed structure
**Migration** — `old/path → new/path`, one line per item
**Docsify Impact** — how the generated sidebar/navbar change
**Validation** — checks performed (§16)

Keep migrations minimal and reversible.

## 16. Validation Checklist

Before finishing:

```
[ ] No unintended content modifications
[ ] No accidental deletions
[ ] No broken internal links
[ ] Sidebar/navbar regenerated; every entry resolves
[ ] No duplicate canonical artifacts
[ ] Naming is consistent
[ ] Project boundaries preserved
[ ] Directory depth reasonable
[ ] Root remains clean, Docsify infra intact
[ ] Navigation (folder README indexes + generated sidebar) is accurate
[ ] SPEC.md remains accurate
[ ] CLAUDE.md remains accurate
[ ] git status contains only intended changes
```

## 17. Do Not Over-Engineer

Don't reorganize to look architecturally sophisticated. Prefer `simple + consistent + scalable` over `deep + granular + theoretically perfect`. The repo should be navigable without understanding its entire taxonomy up front.

## 18. Content vs. Structure

Always distinguish a **structural issue** ("ML notes live under an inconsistent directory") from a **content issue** ("this explanation of gradient descent is wrong"). During organization-only work: fix the first, report the second — don't touch it.

## 19. Agent Decision Hierarchy

```
SPEC.md → existing taxonomy → artifact's primary purpose →
consistency with neighboring artifacts → long-term scalability → minimal migration cost
```

Don't optimize for the shortest path alone.

## 20. Final Principle

Every artifact should answer: *What is this? Why does it exist? Where should similar things go? How can I find it later — on GitHub, and on the Docsify site?*

If the repository can't answer those through its structure, improve the structure — don't compensate with more content.
## 21. Metadata Layer

An optional **overlay** on top of the folder structure: pages can carry YAML front matter so they are discoverable by domain and tag and linked to related pages. Folders remain the primary location; files never move for metadata's sake. Pages without front matter are valid ("legacy").

- Schema and controlled vocabulary: `.docs/metadata/schema.yaml`, `.docs/metadata/taxonomy.yaml`. Add a new domain/tag there *before* using it.
- Tools: `.docs/tools/validate.py`, `check_links.py`, `update_recent.py`, `check_pins.py`, `test_new_page.py`, `generate_index.py`, `stage_site.py` (Python + PyYAML 6.0.2); `page_doctor.py` turns their warnings into a to-do list for the changed pages (open at the line, suggested fixes).
- Generated output (never hand-edit, deterministic): `.docs/generated/` — JSON indexes plus Explore pages. Commit it with the change.

**Add metadata to a page** — put front matter at the very top of the file, nothing else changes:

```yaml
---
id: sequence-models            # explicit, unique, kebab-case; required if the page has or receives relations
title: Sequence Models
summary: How models handle ordered data like text, from RNNs to transformers.   # optional, one line, max 200 chars
level: intermediate            # optional: beginner | intermediate | advanced
type: concept                  # concept | guide | reference | note | problem | project | experiment (definitions in taxonomy.yaml); one, or a list of two: [concept, guide]
status: stable                 # draft | stable | deprecated
domains: [deep-learning]       # from taxonomy.yaml
tags: [rnn]                    # optional, max 5, from taxonomy.yaml
relations:                     # optional; targets are explicit ids
  prerequisites: [deep-learning-basics]
  related: [encoder-decoder-machine-translation]
---
```

Front matter may be partial: every field is optional (defaults: `title` = first H1, `type` = note, `status` = stable); `id` is needed only for pages that take part in relations. `sidebar_label` overrides a page's label in the generated sidebar without touching its heading (one line, warned over 40 characters, unique within its folder, quoted if it contains `: `). `sidebar_group` (on a folder's `README.md` only) names that folder's group in the sidebar instead of the text before the last hyphen in its H1; use it when sibling folders would otherwise share a group name. Same limits as `sidebar_label`. A page that carries only these fields is not indexed.

Reading time is computed (200 wpm over the body, code excluded), never authored. `summary` and `level` feed the Explore lists and the **Start here** page (learning paths from `prerequisites`, quick reads of 10 minutes or less, beginner picks); prerequisites must not form a cycle.

**Choosing domains and tags**

- Domains describe the subject, not the folder. Most pages need one or two.
- A `deep-learning` page does not also get `machine-learning` unless it teaches general ML.
- LLM pages may carry both `generative-ai` and `natural-language-processing`.
- `tabular-data` is a folder, not a domain: pages under `fields/tabular-data/` default to `machine-learning` and `statistics` (recorded under `folder_defaults` in `taxonomy.yaml`).
- A tag needs 2+ pages, or must name a concrete technology (`kind: technology` in `taxonomy.yaml`). Max 5 tags per page; the validator errors above that and warns on single-use tags that are not marked as technology.
- Merge, don't multiply: prefer an existing tag (for example `gpu` covers CUDA, `clustering` covers segmentation) over adding a near-duplicate.

Rules: no YAML comments inside front matter (`gen_sidebar.sh` reads the first `# ` line as the page label); the path-derived fallback id of legacy pages is never a relation target; relations never target git submodule content (submodules are skipped entirely).

**Before pushing:**

```bash
python3 .docs/tools/validate.py        # must report 0 errors
python3 .docs/tools/check_links.py     # must report 0 broken links
python3 .docs/tools/generate_index.py  # then commit .docs/generated
cd .docs && ./gen_sidebar.sh && ./gen_navbar.sh   # only if structure/titles changed
```

CI (`validate-metadata.yml`) runs on PRs to `dev`/`main` and pushes to `dev`, and fails on validation errors, broken internal links, raw HTML that would run in readers' browsers (`<script>`, `<iframe>`, `<object>`, `<embed>`, `on...=` handlers, `javascript:` links outside code; `check_links.py`, a deliberate case needs `<!-- allow-html -->` on the line before), or stale `.docs/generated`. `check_links.py` also warns, one line per page, about pictures without a real description (`![]`, `![image]`, a file name as the description); the warning never fails CI and `--no-alt-report` silences it.

**Deploy:** CI builds a staging copy (`stage_site.py --out _site`) that strips front matter, puts the reading time ("6 min read", every content page but the homepage and folder indexes with a `## Contents` list) and a one-line "Read first / See also / Read next" strip under the title, and publishes that copy. Sources are never rewritten. A local `docsify serve` of the repo hides the front matter on the page (Docsify's front-matter plugin) and in search (`.docs/search.js` strips it), but does **not** show the Related block; to preview the deployed result run `python3 .docs/tools/stage_site.py --out _site` and serve `_site/` (git-ignored).
