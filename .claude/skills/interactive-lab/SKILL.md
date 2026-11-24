---
name: interactive-lab
description: Build an interactive HTML lab for a topic in aCupOfTea (a polished, sandbox-embedded, vanilla-JS explainer with presets, dials, experiments and a verified number check), reusing the probability-statistics lab design system. Use when asked to add a lab, simulator, "interactive page" or experiment to a series, or to extend the labs folder.
argument-hint: <topic or series folder>
---

# Interactive lab

A lab is a small experiment the reader runs inside the page. The reference implementation is `fields/data-science/probability-statistics/labs/` (six labs). `CLAUDE.md` §13 "Interactive labs" and `SPEC.md` win over this file; read them first. Do not copy the security rules here from memory, re-read them.

## When a lab earns its place

- The concept is **a relationship the reader can only feel by moving a number** (a dial changes the answer), or **randomness that must be seen** (a simulation converging).
- One lab per **group of pages** (a folder), not per page. A page links to its group's lab.
- No lab when the page is a procedure, a definition or a command list. A table does that better.
- Ask first: "What will the reader predict, and what surprises them?" No surprise, no lab.

## Files and place

- Folder: `<series>/labs/`. New names `lowercase-kebab-case`. Reuse the shared `lab.css` and `lab-core.js` of that series; a **new series** gets its own copy of the two (a folder's labs share one pair, so the allowlist `<folders>/labs/<name>.html` still holds).
- Per lab: `<name>.html` + `<name>.js`. Vanilla JS, no libraries, no CDN, no inline `<script>`, no inline `style=` attribute (the lab's own CSP forbids it: use utility classes `.mt6/.mt10/.mt12/.mt14/.nom` or CSSOM `el.style.x = ...`).
- Every lab page has its own CSP meta, copied from an existing lab unchanged: `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'`.
- The first `.crumbs a` link is the **host page**: a relative `../../../../#/<root-absolute path>.md` (depth = folders from the repo root). A lab opened on its own redirects there, so it must be the page that embeds the lab (the group's quick guide). Wrong target = the reader lands on a page without the lab.

## Page anatomy (copy `bayes.html` or `permutation.html`)

1. `.top`: breadcrumb pills (host page, "Read Part N") and the theme button. Hidden in embed mode.
2. `.hero`: kicker, one question as the `h1`, a one-line `.lead` that gives the answer's formula in `<code>`. Hidden in embed mode.
3. **Result card first**: the one big number (`.big`, `aria-live="polite"`) and a plain sentence (`.says`). The reader sees the answer before the controls.
4. **Try a situation**: 4-6 preset `.chip`s, each with a `data-n` sentence saying what to notice. Presets are the experiments; the first one reproduces the story page's numbers exactly. Exposed state with `aria-pressed`.
5. **Dials**: `input[type=range]` with `<label for>`, an `<output>`, the end labels and a one-line hint. Use log scales for rates spanning decades.
6. **Show the counts**: the same answer as whole items (waffle, bars, a table in `<details>`), because percentages hide what whole counts show.
7. **Check it with random draws**: a seeded simulation button (`Lab.rng(seed++)`) that prints "simulated X against exact Y" and can be repeated.
8. `details.assume` "What this assumes", then `.foot` back to the series.

## Design rules (the system, do not reinvent)

- Tokens in `lab.css` only (leaf green, kettle orange, sky blue; dark via `:root[data-theme="dark"]` and `prefers-color-scheme`). No raw hex in a lab's markup; no emoji as icons (inline SVG with `aria-hidden`).
- Phone first: one column under 640px, targets at least 44px, no horizontal scroll, `[hidden]` honoured.
- Colour is never the only signal (labels, dot shapes, text next to it). Contrast 4.5:1.
- `prefers-reduced-motion`: no required animation. Charts via `Lab.barChart` with a `title`/aria summary; hover tips from `Lab.hover`.
- Charts: nice y-ticks, a visible zero baseline for bars, the truth marked when the lab can know it.

## Embed mode and sandbox

The lab runs in `sandbox="allow-scripts"` with an opaque origin: **no** `localStorage` without `try/catch`, no parent access, no `window.top`, no popups, no forms. `lab-core.js` handles `?embed=1&theme=` and posts its height; the lab's own code must not depend on either, and must look right with the `.top/.hero/.foot` hidden. Never add `allow-same-origin`, `allow-top-navigation` or `allow-popups` to make something work; change the lab.

## Numbers must be true

1. Pick the page's stated numbers first (the story page and the technical reference already assert them).
2. Check every number the lab shows against Python, **stdlib only** (`fractions`, `statistics.NormalDist`, `math.comb`, enumeration). Exact where possible.
3. The preset that mirrors the story page must show the same figures (for example 9.02%, 90.75%).
4. Random-draw outputs get a tolerance check (seeded, so repeatable). Say in the lab when a value is simulated, not exact.
5. Every experiment card's claim is run, not guessed ("mean 6 to 30.25, median 3 to 4"). A claim that fails the check is rewritten, not softened.

## Wire it into the pages

- Story page(s) of the group: a 6-line block `> ☕ **Try it live.** one sentence` then `[Name lab](/<series>/labs/<name>.html#embed ':ignore')` then `* * *`. No other change to the story text (CLAUDE.md §3).
- The group's **quick guide** and **technical reference**: a `## Try it` section with the embed links, one per lab. This is also where the folder README's "Interactive labs" table must point (`/<folder>/quick-guide.md?id=try-it`, same tab). Never link a README row straight to `labs/*.html`: it opens a new tab, loads the bare page and redirects back.
- Update `fields/.../README.md` "Interactive labs" and the series "Where things live" table.
- Run `python3 .docs/tools/check_all.py --fix`. Add the lab's host path to nothing else: the allowlist is a pattern.

## Verify before hand-off

| Check | How |
|---|---|
| Numbers | The Python script from "Numbers must be true", output pasted into the PR |
| Staged site | `python3 .docs/tools/stage_site.py --out _site`, serve `_site/`, open the host page: the frame loads, sidebar present |
| Embed + standalone | Frame is sandboxed (`allow-scripts` only); opening `labs/<name>.html` directly redirects to the host page; `?standalone=1` shows the bare page |
| Dark and phone | Toggle the theme, resize to 390px: no sideways scroll, nothing clipped |
| Smoke test | `node .docs/tests/smoke.js _site chromium` (needs `playwright`); add a check when a lab brings a new rule |
| Console | No errors, no CSP violations |

Use the `ui-ux-pro-max` skill for visual choices that the system does not already settle; the repo's tokens still win.

## Hand-over

One feature branch from `dev`, one PR into `dev` (labs, their pages and the docs together), Auto-fix on. Say what was run (numbers, browser, smoke) and what was not (WebKit only runs in CI).
