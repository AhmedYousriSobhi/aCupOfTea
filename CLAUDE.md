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

Write internal links **root-absolute** (`/fields/benchmarks/hpl.md`). They resolve on both GitHub and Docsify (`relativePath: false`); `./` and `../` links break on the site.

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

## 12. Root Directory

Keep the root clean: `README.md`, `SPEC.md`, `CLAUDE.md`, `LICENSE`, `.gitignore`, and Docsify/CI infra (`index.html` with the Docsify config, `.docs/` holding the sidebar/navbar and their generators, `.github/`, `.gitmodules`). `.nojekyll` is created by CI at deploy time. No temporary notes, experiments, or project-specific files at the root.

## 13. README and Docsify Navigation

`README.md` files are primarily navigation documents (purpose, structure, links, related projects) — but the root `README.md` also doubles as the Docsify homepage, so keep it welcoming, not just a bare index.

`.docs/_sidebar.md` and `.docs/_navbar.md` are **generated** from the file tree by `.docs/gen_sidebar.sh` / `.docs/gen_navbar.sh`, which CI re-runs on every push to `main`. **Never hand-edit them**: CI overwrites manual edits. To change the site's navigation, change the structure, the page's `# H1` heading (used as its label), or the generator. After any structural change, regenerate them locally and commit the output so the repo matches what CI publishes.

Generator behavior worth knowing: folders without any `.md` page are skipped; git submodules (not checked out in CI) are rendered as external links to their repositories; a `README.md` titled `Overview` is listed first.

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