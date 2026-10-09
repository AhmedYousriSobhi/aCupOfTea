# aCupOfTea Repository Specification

**Status:** Active
**Scope:** Repository organization and information architecture
**Content modification:** Out of scope unless explicitly requested
**Related infra:** Docsify site deployed from `main` via `.github/workflows/deploy-docs.yml` — see §13, §16

## 1. Purpose

`aCupOfTea` is a personal knowledge repository covering AI, machine learning, software engineering, programming, business context, and applied projects.

It is intended to function as a **long-term, searchable knowledge system** — increasingly served as a browsable **Docsify site**, not just a folder tree read on GitHub.

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

This is the **target** conceptual architecture, not a mandate to migrate everything immediately. Migration is incremental and evidence-based (§20).

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
LICENSE
.gitignore
.nojekyll           — required by Docsify on GitHub Pages
index.html           — Docsify entry point
index.html           — Docsify entry point + config (window.$docsify)
.docs/               — _sidebar.md / _navbar.md (generated) + gen_sidebar.sh / gen_navbar.sh
.github/             — deploy workflow (regenerates navigation, publishes gh-pages)
.gitmodules          — project/knowledge submodules
```

Do not treat the Docsify infra files as clutter to be moved — they are load-bearing for the hosted site. Do not place temporary notes, experiments, or project-specific docs at the root.

## 14. Naming Convention

New directories and `.md` pages SHOULD use `lowercase-kebab-case` (`deep-learning`, `used-car-price-estimation`). Code, notebook, and data files keep their own conventions (Python modules can't be kebab-case; scripts and notebooks reference data by filename), and `README.md` keeps its name. Avoid `camelCase`, `PascalCase`, mixed naming, misspellings, unexplained abbreviations. Existing names are only renamed when the benefit clearly outweighs migration cost and link breakage.

## 15. Directory Depth

Hierarchy MUST communicate meaningful distinctions. Avoid nesting like `knowledge/machine-learning/algorithms/supervised/classification/concepts/...` when each level holds almost nothing. Prefer a shallow structure plus a `README.md` index once a folder needs one — the generated sidebar picks it up automatically (§16).

## 16. Index Files & Docsify Navigation

Two navigation layers exist and both must stay accurate:

1. **`README.md` indexes** inside a folder — description, subcategories, links, related projects/technologies. Should not duplicate large amounts of underlying content.
2. **`.docs/_sidebar.md`** — the navigation tree for the rendered Docsify site. It is **generated** from the file tree by `.docs/gen_sidebar.sh` (labels come from each page's `# H1`), and CI regenerates it on every push to `main`. It MUST NOT be hand-edited; regenerate and commit it in the same change as any move/rename/new section so the repo matches what's published.

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

- **Optional:** pages without front matter remain valid and keep working; coverage grows incrementally (§20).
- **Identity:** a page that participates in relations needs an explicit, repo-unique, kebab-case `id`. Ids are independent of the path, so moving a file does not break relations. The path-derived fallback id is read-only and is never a relation target. Any id collision (explicit vs explicit, or explicit vs fallback) is an error.
- **Vocabulary:** `type` ∈ concept, guide, reference, note, tutorial, experiment, resource; `status` ∈ draft, stable, deprecated; relation types are exactly `related` and `prerequisites`; domains and tags are defined in `.docs/metadata/taxonomy.yaml`.
- **Location:** schema, taxonomy, tools and generated data live under `.docs/` (served by GitHub Pages), so the root allowlist (§13) is unchanged.
- **Generated, deterministic:** `.docs/generated/` holds `objects.json`, `domains.json`, `tags.json`, `relationships.json` (with reverse links), `related.json` and the Explore pages. The sidebar gains an additive **Explore** section (Domains, Tags); the folder tree is untouched.
- **Submodules** are never written into and are skipped by the tools; relations may not target their content.
- **Deployment:** the published site is a staging copy with front matter stripped and a "Related" block appended; repository sources are never rewritten.

See `CLAUDE.md` §21 for the contributor how-to.
