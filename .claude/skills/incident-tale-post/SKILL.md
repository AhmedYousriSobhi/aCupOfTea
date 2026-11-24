---
name: incident-tale-post
description: Write or convert a knowledge-base page in the "Incident Tale" style: hook and objectives, an incident story, a wrong turn, a pure-technical dig, a verdict that pays off the hook, a short "Never again" and a Scroll at the end, with deadpan humor and animated SVG sketches. Use for troubleshooting, operations or "why did this happen" pages, or when converting an existing page without losing facts.
argument-hint: <topic or existing page path> | <audience>
---

# Incident Tale

Write for: **$ARGUMENTS**. If the topic or audience is missing, ask; don't guess the audience.

The reader is on a coffee break and can close the tab any second. The page is a short film with a technical backbone: the story keeps them reading, the dig gives them the facts, the verdict pays off the opening. Worked example (read it before writing): `example/slurm-spool-dir-full-example.md` and its `example/images/`. It is a sample outside the site tree; its "SAMPLE" note and missing front matter are not part of the style.

`CLAUDE.md` and `SPEC.md` win over this file. This skill replaces `tech-blog-post` for incident/troubleshooting pages; where the two differ (no table of contents, SVG sketches, the beat order, the ending), follow this one. Everything else in `tech-blog-post` (primary sources, asking before running commands, repo conventions) still applies.

## When it fits

- Fits: a failure with a symptom, a misleading clue and a cause (an error message, a drain, a crash, a slow job).
- A concept page: it fits when a real failure the concept explains can carry the story (the wrong turn is the common misconception), and it is written in the **hybrid**: the incident frames the page and **one analogy carries the explanation**, merged with the technical content, as in `fields/generative-ai/llm-inference-performance/compute-bound-vs-memory-bound.md` (the pizza kitchen). Keep such a page's analogy, scenes and good lines; add the hook, objectives, wrong turn and verdict around them. If no honest incident exists, use `tech-blog-post` instead of inventing drama.
- Never apply it to a page the owner has not asked to convert (`CLAUDE.md` §3): converting rewrites content.

## The beats (fixed order)

| # | Beat | Register | Rules |
|---|---|---|---|
| 0 | **Hook + objectives** | story | 2-4 deadpan sentences in future tense that promise a near-disaster and its cost, not its cause ("Around 03:20, Dana will type one `rm -rf` that would have cost six days of training. She'll have a perfectly reasonable explanation. It will be completely wrong."). Then `**By the end of this page you will be able to:**` and 3-4 bullets, each starting with a verb (Explain, Find, Clean up, Stop) and each answered by a named dig or "Never again" sub-section |
| 1 | **Incident** | story | A scene: time, host, alert text, the exact error as a code block. The protagonist and the stakes (what will be lost). End on the obvious-but-wrong reading of the clue |
| 2 | **Wrong turn** | story | 2-3 escalating attempts, each plausible from the clue alone. The last one is dangerous and a human stops it in time. Recap the attempts in bullets, then end on the one question the dig answers |
| 3 | **The dig** | technical | No protagonist, no plot, no "you". Sub-sections with plain descriptive titles; commands with comments, tables, sources named inline. At most one deadpan line per sub-section. On a concept page the one analogy carries the explanation here (real term named first, analogy second); a troubleshooting page usually needs none |
| 4 | **Verdict** | story | Back to the protagonist with the dig's evidence (show the output that decides it). Name the real cause, fix it the safe way the dig describes, confirm recovery, one callback to the hook, one short closing line |
| 5 | **Never again** | technical | Prevention: options as a table, the config as a listing, habits as bullets. Then the `**Next:**` line |
| end | **The Scroll** | technical | `## 📜 The Scroll (keep this)`: a 4-8 line `text` code block of labelled lines (for example `Reason / Usual cause / Check / Do not / Recover / Prevent`), the last section before References. Never at the top |

**Headings are creative titles in the page's own voice**, like "The pizza place that hired the wrong person", "One number about the kitchen", "Plot twist: there are four walls, not two", "The asterisk that doubles your mistake". **Never use the beat names ("The incident", "The wrong turn", "The dig", "The verdict") as headings, and don't number headings.** A heading teases or states the point of its section; separate sections with `---`.

**Keep the culprit hidden until the dig.** Hook, objectives, Incident and Wrong turn may say the clue is wrong and which layer to look at ("the disk underneath"), never the specific culprit (`/tmp`, leftover job scratch) or its fix. The title may name the misdirection ("...Not About the Spool Directory"), not the culprit.

**Balance:** story beats (0, 1, 2, 4) together are about a quarter of the words; the dig and "Never again" hold the facts. Every technical fact lives in the dig, "Never again" or the Scroll, so a reader who skips the story loses nothing.

## Cast and invented names

- One protagonist: a first name, an unglamorous situation that explains the mistake (new on call, inherited the cluster). One or two side characters at most, each with one job (the person with something to lose).
- Hosts, teams, channels and job IDs are synthetic but realistic (`gpu-node-07`, `#cluster-alerts`, "training team"). With a protagonist, the story uses her name, not "you"; "you" appears only in the objectives.
- Clock times move forward and the stakes stay consistent from hook to verdict.

## Voice

- One narrating voice. **No dialogue between two characters as a device, no narrator characters** (a Sage/Traveller pair was rejected as ping-pong). Slack-style quotes from a bot or colleague are fine: one or two lines each, at most one two-line exchange per page.
- **Real technical terms stay real.** Never rename a tool, flag, file or concept as a creature or metaphor. An analogy may explain an idea after the real term is named; on a concept page, **one analogy carried through the whole page** (scene, mapping table, every section) is the best device we have. Don't switch metaphors per section.
- Humor, in the original page's touch: deadpan consequence ("say goodbye to six days of training"), personified daemons ("the first thing polite enough to notice", "refuses to run jobs it cannot keep track of"), understatement ("It is taking it well."). About one joke per section; **each joke carries a technical point** (cut a gag that explains nothing). In the dig, jokes are about the system, never the cast or the stakes. Keep the original's good lines instead of replacing them.
- Short sentences, active voice, contractions, plain words.

## Structure and scannability

- **No paragraph longer than about 4 rendered lines (about 60 words).** Split into bullets or two paragraphs.
- Table for a natural comparison (finding to meaning, options, two things side by side); bullets for a set of facts; an annotated listing for an inventory (one item per line, `# what it is (source)`). Don't flatten a table into prose, or prose into a table that has one column of value.
- Sections are `##` creative titles separated by `---` (see "Headings"); dig sub-sections are `###` with plain descriptive titles. No numbering, no hand-written table of contents (the deployed site drops it and builds its own).
- A ☕ "Try it before you scroll" pause is optional, once or twice, right before an answer.
- Admonitions (`> [!WARNING]`) only for what would cost data or production; one per page is usually enough.

## Sketches (support the text, never replace it)

- Add a sketch only where text is hard to picture (shared resources, a timeline of attempts, a hidden gap such as `df` vs `du`). Two to five per page; a decorative sketch is cut.
- Each sketch makes sense if skipped: alt text describes it, and an italic caption line under it restates the point. The text around it must already say everything.
- An `.svg` file in `images/` next to the page, kebab-case name, linked page-relative: `![Alt text.](images/shared-disk.svg)`. No inline `<svg>` or raw HTML in the page.
- It is loaded as an image, so: **no `<script>`** (it never runs, and the repo forbids it), no external fonts, images or `@import` (not fetched); use `system-ui, sans-serif`. Put `role="img"` and an `aria-label` on the root `<svg>`.
- Animation: CSS `@keyframes` in a `<style>` inside the file (runs in an image in Chromium, WebKit and Firefox), one idea per sketch, a 3-9 s loop that holds the key frame long enough to read.
- Theme: colors as CSS variables on `:root` (the `<svg>` element), redefined under `@media (prefers-color-scheme: dark)`, and an opaque background `<rect>`. The image may follow the device theme rather than the site's theme menu, so it must read on light and dark pages either way.
- `@media (prefers-reduced-motion: reduce)`: stop every animation and show the frame that carries the point (usually the end state).
- Verify with frozen frames in headless Chromium: copy the SVG, give each animation a negative `animation-delay` and `animation-play-state: paused`, screenshot several moments in light and dark, look at them. Fix clipped labels and low contrast. Say on hand-off if live playback was not watched.

## Facts: what must be true

- Real facts only, from primary sources (docs, man pages, source, release notes), named inline and linked in References. Pin versions where behavior differs.
- The scenario (hosts, people, timeline) may be invented; technical claims and numbers may not. Disclose the invented scenario once in the opening blockquote; mark the author's own reading ("the page author's reading of the design: verify it on a test node").
- **The story obeys the dig.** Re-read every story action against it (example of a caught bug: deleting more files cannot free space held by a deleted-but-open file while the process runs). The verdict's fix must be the safe procedure the dig gives.
- **No confidential material.** Synthetic hosts, people, teams; no ticket IDs, company names, vendor programs, internal paths or IPs. Replace them silently.
- Don't run commands on hosts without asking. If code was tested earlier, say on the page what was and wasn't re-run.

## Converting an existing page (no fact may be lost)

1. Get the owner's go-ahead (`CLAUDE.md` §3). Convert **in place**, at the same path: no second copy (§9). Keep the front matter; update `title` to the new H1 and keep `id`, `order`, `sidebar_label`, `summary`, `relations`.
2. List every command, flag, config key, file name, number, version, source, person, quoted phrase, caveat and link in the original.
3. Place each: troubleshooting pages map almost 1:1 (symptom to Incident, misconception to Wrong turn, explanation and runbook to the dig, prevention to "Never again", cheat sheet to the Scroll). For a concept page, the explanation is the dig and the incident is the smallest real failure it explains.
4. Check mechanically that every inline-code token, link and number of the original is in the new page (grep as plain text: a token moved into a listing loses its backticks); then read for qualitative facts (attributions such as which source said what, quotes, caveats). Report anything left out, and report content problems in the original separately without fixing them.

## Endings, series and front matter

- `**Next:**` closes "Never again": one question the reader now wants answered, then a root-absolute link. In a series, link the next page by `order`; on the last page, link the most related page and say so. Don't hand-write "See also", "Read next" or "Last updated": the site adds them.
- New pages: create them with `python3 .docs/tools/new_page.py` (front matter `id`, `title`, `type` (usually `guide`), `domains`, `summary`, `level`, `tags` from `taxonomy.yaml`, `order` in a series, `relations`).
- File names kebab-case; internal links root-absolute; images page-relative. Fences use a language `index.html` loads (bash, python, powershell, yaml, c, ini, sql) or `text` for output and listings.
- One feature branch from `dev`, one PR into `dev`. Before finishing: `python3 .docs/tools/check_all.py --fix`, then `new_page.py --check PAGE`.

## Length

The 5-8 minute target is a soft guide. A longer page is fine **if it reads light**: short paragraphs, a joke or a sketch every screen or two, no section a bored reader would skim. Trim in this order: repeated points, story that carries no fact, then a sketch that repeats a table. Never trim facts of a converted page.

## Review before hand-off

1. Self-score against the rubric, with evidence (a quote or line number) for every score.
2. If the owner agrees to an independent review, give the reviewer the original and the draft (files, not your conclusions) and ask for a fact audit plus a beat and engagement critique.

| Criterion | 10 means |
|---|---|
| Fact fidelity | Every fact and attribution of the source kept, nothing technical invented, sources named |
| Beat structure | Beats in order, dig pure technical, cause hidden until the dig, verdict pays off the hook |
| Hook and pull | The hook promises a cost; each beat ends on a pull; objectives match sections |
| Humor | About one deadpan joke per section, each carrying a technical point |
| Scannability | No paragraph over about 4 lines; tables, bullets, listings where they fit |
| Visuals | Sketches support the text, caption restates the point, themes and reduced motion work, frames checked |
| Reading feels light | Long only where it earns it; nothing a reader would skim; minutes reported by `--check` |
| Honesty and safety | Scenario disclosed once, author's reading flagged, unverified items stated, nothing confidential |

Hand over with one line naming the audience as you understood it and anything unverified.
