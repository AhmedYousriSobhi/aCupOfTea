# aCupOfTea Repository Specification

**Status:** Active
**Scope:** Repository organization and information architecture
**Content modification:** Out of scope unless explicitly requested
**Related infra:** Docsify site deployed from `main` via `.github/workflows/deploy-docs.yml` — see §13, §16, §26, §27

## 1. Purpose

`aCupOfTea` is a personal knowledge repository covering AI, machine learning, software engineering, programming, business context, and applied projects.

It is intended to function as a **long-term, searchable knowledge system** — increasingly served as a browsable **Docsify site**, not just a folder tree read on GitHub.

Two goals guide every structural decision:

1. **Share knowledge.** Pages are written from real experience and read like a short blog: a reader (first of all the author, coming back to recall something) should find a page, finish it in a coffee break, and find the next related page. The rendered site, including on a phone, is the primary reading surface.
2. **Make adding knowledge easy.** A new page should take one command or one markdown file, with navigation, indexes and search updating without hand-editing (§27).

When a proposal does not serve one of these goals, prefer not doing it (§25).

This spec defines how information is *organized*. It does not define the technical correctness of any individual document's content.

## 2. Design Principles

The repository MUST prioritize, in no particular order: clear information architecture, discoverability, consistent naming, low directory complexity, separation of concerns, a single source of truth per artifact, project isolation, long-term scalability, Git-friendly changes, human-and-AI maintainability, and a coherent Docsify navigation experience.

## 3. Primary Content Types

| Type | Purpose |
|---|---|
| Concept | Explains an idea, theory, principle, or technique |
| Technology | Describes a tool, framework, library, or platform |
| Engineering | Software/system engineering practice |
| Problem | A reusable problem formulation |
| Project | A concrete implementation addressing a defined problem |
| Experiment | Exploratory or temporary investigation |
| Business | Business-domain or product knowledge |
| Reference | Lookup-oriented material |
| Decision | A recorded decision and its rationale |

Every substantive artifact SHOULD have exactly one canonical location, classified by its **primary purpose**.

## 4. Conceptual Repository Model

```
aCupOfTea/
│
├── knowledge/
│   ├── foundations/
│   ├── machine-learning/
│   ├── deep-learning/
│   ├── generative-ai/
│   └── reinforcement-learning/
│
├── engineering/
│   ├── programming/
│   ├── clean-code/
│   ├── design-patterns/
│   ├── architecture/
│   ├── testing/
│   └── performance/
│
├── technologies/
├── problems/
├── projects/
├── experiments/
├── business/
├── references/
└── decisions/
```

This is the **target** conceptual architecture, not a mandate to migrate everything immediately. Migration is incremental and evidence-based (§19).

**Current top-level layout** (the implementation today):

| Folder | Holds | Target equivalent |
|---|---|---|
| `fields/` | subject knowledge, plus some technology notes (`libraries-frameworks-containers/`) and infra topics (`benchmarks/`, `schedulers/`, `system-administration/`) | `knowledge/`, `technologies/` |
| `programming/` | programming and software-engineering practice | `engineering/` |
| `problems/` | reusable problem formulations and interview problems | `problems/` |
| `projects/` | projects (mostly git submodules) | `projects/` |
| `experiments/` | exploratory notebooks/codebases | `experiments/` |
| `business/` | business-domain knowledge | `business/` |
| `tips/` | quick tips and lookups | `references/` |
| `journal/` | dated notes | — |

## 5–13 Content Type Rules

**Knowledge** — organized by subject, not by the project it was originally learned from.
**Engineering** — reusable practices; don't bury generally-useful engineering knowledge inside one project.
**Technologies** — organized around a specific tool/library. NOT a dumping ground for every file that happens to import it; primary subject still determines placement.
**Problems** — reusable problem formulations independent of any single implementation.
**Projects** — first-class artifacts with their own objective, implementation, dependencies, results, and docs. Never relocated into a technology folder just because it uses that technology.
**Experiments** — lightweight, exploratory; promotable to `projects/` once they mature.
**Business** — business models, KPIs, stakeholders, AI opportunities, domain constraints — separated from implementation detail.
**References** — cheat sheets, terminology, external links; never a substitute for organizing real knowledge.
**Decisions** — durable architecture/methodology calls: context, decision, reason, alternatives considered, consequences.

## 13. Repository Root & Docsify Infrastructure

The root SHOULD contain only genuinely repository-wide files:

```
README.md          — repo overview AND Docsify homepage
SPEC.md
CLAUDE.md
LICENSE             — CC BY 4.0, for writing and diagrams
LICENSE-CODE        — MIT, for code (scripts, notebooks, .docs/ tooling)
.gitignore
index.html           — Docsify entry point: page shell, styles, Content-Security-Policy; settings in .docs/config.js
.docs/               — site infrastructure:
                         _sidebar.md / _navbar.md (generated) + gen_sidebar.sh / gen_navbar.sh
                         search.js (site search)
                         image-viewer.js (phone image viewer)
                         phone-tables.js (phone table cards)
                         lazy-images.js (images load as you scroll)
                         _404.md (page shown for a missing link)
                         page-footer.js (Edit this page, Last updated, Copy share link)
                         math.js (display formulas with KaTeX)
                         config.js (Docsify settings, window.$docsify)
                         lazy-libs.js (loads Mermaid and KaTeX only on pages that use them)
                         reading-progress.js (progress bar, back-to-top button)
                         surprise-me.js (random page link in the menu)
                         reading-history.js (pages read get a check in the menu, Continue link, Save for later and the Saved list)
                         section-links.js (copy a link to an h2/h3 section)
                         offline.js + sw-template.js (read offline; stage_site.py writes sw.js into the published copy)
                         theme-toggle.js (theme list: light, sepia, dark, midnight, black)
                         sidebar-groups.js (open/close menu folders)
                         page-outline.js (On this page list, wide screens)
                         icons/ (favicon.svg, PNG sizes, site.webmanifest)
                         tests/smoke.js (browser smoke test of the staged site, run in Chromium and WebKit)
                         metadata/ (schema.yaml, taxonomy.yaml)
                         tools/ (check_all, validate, generate_index, stage_site, code_pages, build_search_index, optimize_images, share_pages, check_links, update_recent, check_pins, new_page, page_doctor, page_gui (+ page_gui.html), and the test_*.py files that CI runs)
                         generated/ (indexes and Explore pages, generated)
                         hooks/pre-commit (regenerates sidebar, navbar and indexes on commit; opt in with core.hooksPath)
.github/             — workflows (validate metadata, smoke test, pin check; deploy a staged copy to gh-pages), dependabot.yml (action updates) and CONTRIBUTING.md
.gitmodules          — project/knowledge submodules
```

`.nojekyll` is not committed: the deploy workflow creates it in the published copy.

Do not treat the Docsify infra files as clutter to be moved — they are load-bearing for the hosted site. Do not place temporary notes, experiments, or project-specific docs at the root.

## 14. Naming Convention

New directories and `.md` pages SHOULD use `lowercase-kebab-case` (`deep-learning`, `used-car-price-estimation`). Code, notebook, and data files keep their own conventions (Python modules can't be kebab-case; scripts and notebooks reference data by filename), and `README.md` keeps its name. Avoid `camelCase`, `PascalCase`, mixed naming, misspellings, unexplained abbreviations. Existing names are only renamed when the benefit clearly outweighs migration cost and link breakage.

## 15. Directory Depth

Hierarchy MUST communicate meaningful distinctions. Avoid nesting like `knowledge/machine-learning/algorithms/supervised/classification/concepts/...` when each level holds almost nothing. Prefer a shallow structure plus a `README.md` index once a folder needs one — the generated sidebar picks it up automatically (§16).

## 16. Index Files & Docsify Navigation

Two navigation layers exist and both must stay accurate:

1. **`README.md` indexes** inside a folder — description, subcategories, links, related projects/technologies. Should not duplicate large amounts of underlying content.
2. **`.docs/_sidebar.md`** — the navigation tree for the rendered Docsify site. It is **generated** from the file tree by `.docs/gen_sidebar.sh`, and CI regenerates it on every push to `main`. It MUST NOT be hand-edited; regenerate and commit it in the same change as any move/rename/new section so the repo matches what's published.
   - Inside a folder the README comes first, then pages with an `order` (front matter, §26) by that number, then the rest alphabetically; Previous/Next follow the sidebar.
   - A page's label is the text after the last hyphen of its `# H1` (the whole H1 if it has none). A `sidebar_label` in front matter overrides it without editing the heading.
   - A folder's group name is the text before the last hyphen of its `README.md` H1, and the group heading links to that README (the README is not repeated as a child entry; the chevron folds the group). A `sidebar_group` in that README overrides it; use it when sibling folders would share a name.
   - An additive **Explore** section (Start here, Domains, Tags) comes from the metadata layer (§26); the folder tree below it is untouched.

Folder `README.md` indexes SHOULD list their pages in a `| File | Description |` table under `## Contents`, the format `new_page.py` updates automatically (§27). Converging the remaining list-style indexes is tracked in issue #77.

**Search** (`.docs/search.js`) indexes the pages listed in the generated sidebar, so any page reachable from the sidebar is searchable with no extra step. On the deployed site the text comes from one prebuilt file, `.docs/search-index.json`, which `stage_site.py` writes into the published copy (never committed); a local preview has no such file, so the search reads every page instead and gives the same results.

The sidebar governs what's reachable on the site; the folder `README.md` governs what's understandable when browsing the raw repo. Keep README indexes in sync with the folder contents.

**Link style:** internal links MUST be root-absolute (`/fields/benchmarks/hpl.md`), which resolve on both GitHub and Docsify (`relativePath: false`). Relative `./`/`../` links break on the site.

## 17. Canonical Location & Duplicate Prevention

Every substantive artifact has one canonical location. If it's relevant from multiple angles, prefer **canonical document + cross-reference** over copies. Never duplicate knowledge into multiple categories just to make it independently discoverable — link to it from the relevant README indexes.

## 18. Projects vs. Knowledge

| | Answers |
|---|---|
| Knowledge | "What is this?" |
| Problem | "What are we solving?" |
| Technology | "What tool implements it?" |
| Project | "What did we build?" |
| Experiment | "What did we investigate?" |
| Decision | "Why this approach?" |

This distinction MUST guide all future placement decisions.

## 19. Migration Rules

Structural migrations MUST: preserve file content · prefer `git mv` · preserve project boundaries · update internal references (including absolute self-repo GitHub URLs) AND regenerate the sidebar/navbar · check for broken links · avoid unnecessary renames · avoid deleting substantive material · stay reviewable · be incremental rather than one giant restructure.

Changes flow `feature branch → dev → main`: each feature is developed on its own branch cut from `dev` and merged into `dev` by PR. `main` MUST only be updated by a `dev → main` PR, because every push to `main` redeploys the published site.

## 20. Ambiguous Content

If classification is unclear: **do not silently guess.** Record the ambiguity, list the plausible classifications, and let a human decide.

## 21. Content Preservation

During organization-only work: **content = immutable, structure = mutable.** Agents may reorganize; agents must not rewrite substantive content unless explicitly instructed.

## 22. Validation Requirements

Before considering a structural change complete, verify:

```
[ ] No accidental content modification or deletion
[ ] No broken internal links
[ ] Sidebar/navbar regenerated; no broken entries
[ ] No duplicate canonical locations
[ ] Naming conventions respected
[ ] Project boundaries preserved
[ ] Directory depth reasonable
[ ] Root directory still clean (incl. Docsify infra intact)
[ ] README.md indexes / generated sidebar reflect current structure
[ ] .docs/tools/validate.py reports 0 errors; .docs/generated is regenerated and committed
[ ] SPEC.md and CLAUDE.md remain accurate
[ ] Git history preserved where practical
```

## 23. Scalability Rule

The taxonomy MUST remain usable if the repository grows by an order of magnitude. Don't create categories solely for today's contents; prefer stable conceptual categories over highly specific one-off folders.

## 24. Source of Truth

When architectural ambiguity exists, priority is:

```
SPEC.md → CLAUDE.md → repository structure (and its generated navigation) → existing content
```

`SPEC.md` defines the intended architecture. `CLAUDE.md` defines operational behavior for AI agents. The repository (including its Docsify navigation) is the implementation of both.

## 25. Change Philosophy

The goal is not a "perfect" directory tree — it's a structure that is understandable, predictable, searchable, maintainable, scalable, and renders correctly as a Docsify site. Structural simplicity beats theoretical purity.
## 26. Metadata Layer

Content type, location and navigation are unchanged; metadata is an **overlay** that lets one page be discovered under several domains/tags and linked to related pages. Markdown + YAML front matter is the only source of truth; there is no database or service.

- **Optional:** pages without front matter remain valid and keep working; coverage grows incrementally (§19, §23).
- **Identity:** a page that participates in relations needs an explicit, repo-unique, kebab-case `id`. Ids are independent of the path, so moving a file does not break relations. The path-derived fallback id is read-only and is never a relation target. Any id collision (explicit vs explicit, or explicit vs fallback) is an error.
- **Reader aids:** optional `summary` (one line, max 200 chars) and `level` (beginner, intermediate, advanced) are authored; reading time is computed. They drive the Explore lists and a generated **Start here** page (learning paths from prerequisite chains, quick reads, beginner picks). Prerequisites must be acyclic.
- **Vocabulary:** `type` (one value, or a list of at most two with the main one first) ∈ the kinds defined in `taxonomy.yaml` (concept, guide, reference, note, problem, project, experiment to start with; a new kind is added there with a one-line definition); `status` ∈ draft, stable, deprecated; relation types are exactly `related` and `prerequisites`; domains and tags are defined in `.docs/metadata/taxonomy.yaml`. A tag needs 2+ pages or must name a concrete technology, and a page carries at most 5 tags. Domain overlap rules (deep-learning vs machine-learning, generative-ai with natural-language-processing) are in `CLAUDE.md` §21.
- **Location:** schema, taxonomy, tools and generated data live under `.docs/` (served by GitHub Pages), so the root allowlist (§13) is unchanged.
- **Generated, deterministic:** `.docs/generated/` holds `objects.json`, `domains.json`, `tags.json`, `relationships.json` (with reverse links), `related.json` and the Explore pages. The sidebar gains an additive **Explore** section (Start here, Domains, Tags); the folder tree is untouched.
- **Submodules** are never written into and are skipped by the tools; relations may not target their content.
- **Link previews:** the staged copy also holds a share page per content page at its folder address (title and summary as Open Graph tags, then a redirect to the `#/` page), so a shared link previews that page; `summary` in front matter feeds the description, else the first paragraph is used.
- **Deployment:** the published site is a staging copy with front matter stripped and a "Read first / See also / Read next" strip under the title; repository sources are never rewritten.
- **Reading order:** optional `order` (whole number from 1 up, unique within a folder) is a page's position in its folder: it drives the generated sidebar, the Previous/Next buttons, the "Read next" strip and Start here paths. A prerequisite in the same folder should have a smaller number.
- **Partial front matter, `sidebar_label` and `sidebar_group`:** every field is optional (defaults: title = first H1, type = note, status = stable); `id` only for pages in relations. `sidebar_label` overrides a page's sidebar label without editing its heading; `sidebar_group` (folder `README.md` only) overrides the folder's group name. Labels must be unique within a folder and groups among sibling folders. A page with only these fields is not indexed and gets no domain.

See `CLAUDE.md` §21 for the contributor how-to.

## 27. Adding New Knowledge

**Finishing any change:** `python3 .docs/tools/check_all.py --fix` runs the validation suite (front matter, links, tests) and regenerates the indexes, sidebar and navbar; CI runs the same script without `--fix` on every PR to `dev`/`main` and push to `dev`, so a stale generated file or a broken rule blocks the merge.

Adding a page MUST stay a small, repeatable step for a solo author or an outside contributor:

- **Preferred:** `python3 .docs/tools/new_page.py`. It asks for a title, optional summary, folder, type, domains (suggested from the folder), tags, level, prerequisites and related pages, then creates the kebab-case file with front matter and a short outline, adds the page to the folder's `README.md` table, and regenerates the sidebar and navbar. It suggests the closest existing folders, warns about similar existing pages (§17), never overwrites a file, and never creates a folder without confirmation (§15). New tags are added to `taxonomy.yaml` only after confirmation (§26). Reading time is never entered: the site computes it from the text, and `new_page.py --check PAGE` shows it together with what is still missing.
- **In the browser:** `new_page.py --gui` serves the same questions, the hand-written-page flow and the `page_doctor.py` list (similar problems grouped under one heading) as a form on 127.0.0.1 only (`page_gui.py`, `page_gui.html`); it runs `new_page.py` with options, so the rules are the same.
- **Changing metadata later:** `new_page.py --update PAGE` changes the summary, kind, subjects, tags, level or relations of a page that has front matter, keeping every other field and the page text.
- **A page written by hand:** `python3 .docs/tools/new_page.py --adopt PAGE` adds the front matter and index link to an existing page without changing its text, and, for a page with partial front matter, keeps it and adds only the missing fields.
- **Without the script:** create a kebab-case `.md` file with one `# H1`, add it to the folder's `README.md` index, and regenerate the sidebar. Front matter stays optional.
- **Code files and notebooks** (`.py`, `.ipynb`, ...) linked from a page open as readable pages on the site: `stage_site.py` writes `name.py.md` / `name.ipynb.md` in the published copy (`code_pages.py`), so link them root-absolute like pages and nothing else is needed.
- **Images** for new pages SHOULD be committed next to the page (for example `images/` in the same folder) rather than linked from other sites, which can disappear. Moving existing linked images into the repo is tracked in issue #82.
- **Contributor steps** live in `.github/CONTRIBUTING.md`; changes go through a feature branch and a PR into `dev` (CLAUDE.md §11).
