---
name: tech-blog-post
description: Write a technical blog post or numbered series in Markdown for engineers, in a story-first, funny, senior-engineer-over-coffee voice with diagrams and reader pauses, and primary-source rigor. Use when asked to write a post, guide, tale, or series page for this knowledge base.
argument-hint: <topic> | <audience, e.g. HPC admins comfortable with a root shell>
---

# Technical blog post / series

Write for: **$ARGUMENTS**

If the topic or audience is missing from the arguments, ask for them before writing. Don't guess the audience.

## Voice

- Fun, direct, confident, like a senior engineer explaining things over coffee. Never a lecture, never a grandma.
- Humor comes from vivid real-world scenarios and analogies, not jokes. Open with a concrete failure story ("cn042 lost its /scratch mount at 23:10, and by morning 400 jobs had died").
- Short sentences. Active voice. Say "you". Use contractions.
- Plain words over jargon. When a term is needed, define it in one line the first time.
- Opinionated: recommend one way, say why, and name the trade-off. No "it depends" without saying what it depends on.

## The story-first voice (the page must pull the reader to the end)

The reader is on a coffee break and can close the tab any second. Write so that stopping feels like leaving a film halfway. The benchmark is `fields/generative-ai/llm-inference-performance/llm-inference-on-the-roofline.md` (named for its topic, the Roofline performance model, not for a style). Read it before writing a series, and match these moves:

1. **Open with a scene, not a summary.** Two support tickets, a 3 AM page, a junior engineer who closes the ticket with the wrong fix. Invented clients, hosts and tickets are fine; invented numbers are not.
2. **One analogy, carried the whole way.** Pick one picture (a librarian, a bus, kitchens and chefs) and let every section advance both the picture and the technical point. Do not switch metaphors per section, and do not use a gimmick (such as "TV seasons") as a costume for a list.
3. **End sections on a question or a cliffhanger** that the next section answers ("So why was Ticket 1 a different problem?"). The reader should never reach a section end with nothing pulling them on.
4. **Add a "Try it before you scroll" pause** (☕, about ten seconds) once or twice per page, just before the answer: a small guess-the-result question with a one-line hint. Put the answer in the next section, or directly below for a quiz.
5. **Callbacks.** Return to the opening scene near the end ("Back to the two tickets") and give a verdict. Refer to earlier parts by their picture, not just their number.
6. **Short punch lines.** "One." "Single digits. At any batch size." Humor comes from the scenario and from a joke that also carries the technical point; a gag that explains nothing gets cut.
7. **Close with a challenge**, not a recap: a question the reader can now answer, leading to the next part.

Do not write a changelog. Versions, dates and history become **tickets with verdicts** ("mostly no, with one caveat") or a story with stakes, with the dates in a small table.

## Structure (every page)

1. H1 title, then a one- or two-sentence blockquote that starts with a bold **Part N of M.**: the hook, and what the reader will have by the end.
2. A linked table of contents.
3. Sections separated by horizontal rules. Each section either teaches one idea or completes one step.
4. Guide steps are numbered, copy-paste ready, and say what success looks like (expected output, exit code).
5. Use tables for comparisons, options, symptom → cause → fix, and question → why it matters.
6. Use GitHub admonitions sparingly: `> [!TIP]`, `> [!NOTE]`, `> [!WARNING]`, `> [!IMPORTANT]`, `> [!CAUTION]`. Only for things that would cost the reader time or break production.
7. End with a one-line bold **Takeaway:**, then a question or challenge that links to the next part (for the last part: a closing challenge plus a link to related pages), then a References list.
8. Aim for 5-7 minutes of reading per page (`new_page.py --check`). Over 8 minutes, trim the least useful section first.

## Technical rigor (non-negotiable)

- Every fact comes from a primary source: official docs, man pages, vendor spec sheets, source code, release notes. Link them in References.
- Real specs only. If an example needs hardware, use real products and cite their documentation. Invented names are fine for clients and hosts; invented numbers are not.
- **Ask the user before running any command or script** (it may touch hosts, clusters, or services). Once approved, every command and script must actually run. Test code before publishing, including the failure path: prove a check fails when it should, not just that it passes. If you can't run something, say so on the page and in your hand-off; never present untested output as real.
- When testing finds a bug or a surprising behavior, say so on the page. "Here's the trap and how we found it" is the most valuable content.
- Pin versions ("written against X 1.5"). Note where older versions behave differently.
- Distinguish clearly between what the docs say, what testing showed, and what you recommend.

## Content patterns

- Explain why before how: the problem, the mental model, then the steps.
- Call out gotchas where the reader will hit them, not in a list at the end.
- Show real output in code blocks, including errors.
- Give rules of thumb a name or a one-liner ("the more often a check runs, the cheaper it must be").
- **Show it, don't only tell it.** Put at least one picture on any page that explains a structure or flow (shared vs separate memory, a pipeline, where threads land on CPUs). Use a Mermaid diagram (see Formatting) or a small table; a wall of code with no picture is a sign the page is not done.
- **Annotate code listings** with short inline comments that say what each line does for the reader's mental model (`/* FORK: runs once per thread */`), then explain the one or two lines that matter. Adding comments to code you already tested does not change its behaviour, but compile the commented listing again when you can.
- **Reference sections** (cheat sheets, "how to spot X") are allowed, but give them a scene or a quiz so they don't read like a man page.
- Say what the tool is NOT for.
- For anything risky, include a safe path: dry run → canary → enforce, with a rollback.

## Formatting

- Markdown only. Code blocks always have a language tag.
- Bold for key terms on first use, not for decoration.
- No filler intros ("In today's fast-paced world..."), no recap paragraphs, no emojis except a rare one with a purpose (☕ for a pause).
- **Diagrams:** Mermaid fences only (`flowchart`, `sequenceDiagram`, `stateDiagram-v2`; the site pins Mermaid and loads it on demand). Keep labels short, use `<br/>` for line breaks, quote labels with `["..."]`, and avoid `#` and `;` inside labels. Prefer few nodes, one idea per diagram, and a one-line caption under it. Use a `subgraph` to show "these things share a box" instead of crossing lines everywhere. Always **render-test**: load the pinned Mermaid version in headless Chromium (Playwright in a scratch folder), check there are no errors, and look at the picture. A diagram that parses can still be a tangle.
- Keep each page finishable in one sitting. Split long topics into a numbered series with consistent navigation (same header blockquote, same "Next:" link at the end).

## Repo conventions (aCupOfTea)

Follow `CLAUDE.md` and `SPEC.md`; they win over anything here.

- **Placement:** read `SPEC.md` §3 and the target folder's `README.md` first. Put the page in the existing canonical folder for the topic. Don't create new directories for one page.
- **Creating the page:** use `python3 .docs/tools/new_page.py` (or `--adopt PAGE` for a hand-written file). It writes front matter, adds the folder README row, and regenerates the sidebar and navbar.
- **Front matter:** `id`, `title`, `type`, `domains`, optional `summary` (one line, max 200 chars), `level`, `tags`, `order` (give every page of a series one), `relations`. Use only domains and tags from `.docs/metadata/taxonomy.yaml`. No YAML comments inside front matter.
- **File names:** `lowercase-kebab-case.md`. The `# H1` becomes the sidebar label.
- **Links:** root-absolute (`/fields/schedulers/page.md`), never `./` or `../`. Images are page-relative (`images/name.png`, with a real alt text).
- **Math:** a line that is only `$$...$$` renders as a display formula. Fences need a Prism language that `index.html` loads (bash, python, powershell, yaml, c, ini, sql); otherwise use `text`.
- **No raw HTML** such as `<script>`, `<iframe>`, or `on...=` handlers.
- **Git:** one feature branch cut from `dev`, one PR into `dev`. Never push to `main`. Related pages requested together share one branch and one PR. Don't stack PRs.
- **Before finishing:** run `python3 .docs/tools/check_all.py --fix`, then `new_page.py --check PAGE` for reading time and missing metadata. Commit what the generators update.
- Don't modify existing pages' content unless asked. Report content problems separately.

## Workflow

1. Confirm topic and audience. Skim neighboring pages in the target folder for series position, tone, and links.
2. Gather primary sources first. Note the exact versions you write against.
3. Outline: scene opening, the one analogy, mental model, numbered steps, gotchas, where a ☕ pause and a diagram go, safe path, takeaway, closing challenge.
4. List the commands you need to verify and ask the user before running them. Run the success path and the failure path.
5. Write the page, with every surprise you hit on the page. Then reread it as a bored reader: where would you stop reading? Add a hook or a picture there, or cut.
6. Render-test every diagram. Run the repo checks above. Hand over with one line naming the audience as you understood it, plus anything untested.
