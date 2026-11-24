---
name: quick-guide
description: Write the direct "quick guide" companion of a story page in aCupOfTea: a short cheat-sheet-plus-steps page (about 300-600 words) with numbered copy-paste steps, expected output, a symptom table and a rollback, built only from facts already on the story page. Use after writing or converting a page with the incident-tale-post skill, or when asked for a cheat sheet or direct steps for an existing page.
argument-hint: <story page path>
---

# Quick guide

The story page is for the coffee break. The quick guide is for the person who is already at the terminal and wants the answer now. **One quick guide per subfolder** (not per story page): it covers every story page of that folder in order, as its own page named `quick-guide.md` in that folder, with one Part per story page and a single shared Before-you-start, symptom table and roll-out section. A folder with one story page gets a guide for that page. No story, no analogy, no jokes: it is a tool, not a tale.

`CLAUDE.md` and `SPEC.md` win over this file. Story pages follow `incident-tale-post`; this skill only covers the companion.

## When to write one

- Every new or converted story page that has commands, thresholds or a procedure gets a quick guide.
- Pure concept pages with nothing to run (no commands, no steps) get none; their Scroll is enough.
- A folder gets one quick guide with a Part per story page; its Parts stay separate so each still answers one question.

## The one rule: no new facts

- Every command, flag, config key, threshold, number and warning in the quick guide must already be on the story page (the source of truth). Never add a fact here first.
- Restate, don't explain: no "why". The "why" is one link away.
- After writing, check mechanically that every inline-code token and number of the quick guide appears on the story page, and report any that do not.
- If the story page has a fact you cannot state in one line, leave it out and let the link carry it.

## Shape of the page (300-600 words, under 3 minutes)

1. **H1:** the task as a verb phrase ("Add a GPU temperature ceiling to a health check"), not a tale title.
2. **Opening blockquote, two lines:** `**Quick guide for** [story title](/path.md).` then when to use it and what you will have at the end. Add the one-line scenario disclosure only if the story page invents one the guide mentions (it usually should not).
3. **Before you start:** 2-4 bullets (access, tools, versions, what must be true). Plain.
4. **Steps:** numbered, one action each. Each step is a command block, then `**Expect:**` (the output or exit code that means success), then `**If not:**` (the one fix or the pointer). No step without an expectation.
5. **Tips and tricks:** 3-7 bullets of shortcuts and habits that save time, each already on the story page (a cron email, a flag, a config that prevents the problem). Plain, one line each.
6. **Warnings:** one `> [!WARNING]` for the thing that costs data or production, then bullets for the traps and fine print the story page names (what is not undone, what silently does not happen, what locks you out). Say what is untested if the story page does.
7. **Symptom table:** `What you see | Likely cause | Fix`. A table because it is a comparison; 3-6 rows.
8. **Safe path:** dry run, canary or alert-only first if the action can hurt, and a **Roll back** line that undoes it. State what NOT to do in one line (`**Don't:**`).
9. **The Scroll (optional):** a 4-8 line `text` block if the story page's Scroll already says it better; otherwise skip it. Never repeat a table twice.
10. **Footer:** `**Why it works:** [story page](/path.md)` and a link to the sibling quick guide or next step. The story page, in turn, links back with `**Just the steps:** [quick guide](/path.md)` (add that line to the story page only when the owner agrees to edit it).

## Headings and style

- Plain functional headings (`Before you start`, `Steps`, `Tips and tricks`, `Warnings`, `If it fails`, `Roll back`). Creative titles are for story pages.
- Imperative voice, short sentences, no jokes, no analogy, no characters, no scenario.
- No paragraph over about 3 lines; bullets and tables over prose.
- No sketch unless the flow is non-linear and a picture saves a paragraph; at most one, with a caption that restates the point.
- No table of contents.

## Repo conventions

- File name `quick-guide.md`, in the subfolder it covers; links root-absolute. Word budget grows with the parts (about 400 words per story page).
- Create with `python3 .docs/tools/new_page.py` (or `--adopt PAGE`): front matter `id` (`<story-id>-quick`), `title`, `type: [guide, reference]`, `domains` and `level` from the story page, a one-line `summary`, `tags` from `taxonomy.yaml` (the `quick` tag must be added there first, and a tag needs 2+ pages), `order` right after its story page's neighbors, `sidebar_label` like `Quick guide: <topic>` (unique within the folder), `relations.related: [<story ids>]`.
- The folder README gets its row from `new_page.py`; check `new_page.py --check PAGE` for reading time (aim under 3 minutes).
- Run `python3 .docs/tools/check_all.py --fix` before finishing. One feature branch from `dev` with the story pages it belongs to; one PR into `dev`.

## Review before hand-off

| Criterion | 10 means |
|---|---|
| Direct | The reader can finish the task without reading the story page |
| No new facts | Every token and number is on the story page (checked mechanically) |
| Every step verifiable | Each step has an expected result and a fix |
| Safe | Rollback and one "Don't" for anything risky |
| Short | Under 600 words, no paragraph over 3 lines |
| Linked | Points to its story page and sibling, and nothing else duplicated |

Hand over with one line naming the reader as you understood them and anything unverified.
