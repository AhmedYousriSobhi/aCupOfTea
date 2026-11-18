#!/usr/bin/env python3
"""Link the first use of each glossary term on a page to its entry (staged site only).

`references/glossary.md` has one `## TERM` section per term, starting with the
expansion in bold (`**Message Passing Interface.** ...`). In every other staged
page, the first use of each term becomes
`[MPI](/references/glossary?id=mpi "Message Passing Interface")`: a plain link,
so it works on touch screens (no script), and the title is the hover tooltip.

Only exact, case-sensitive whole words are linked, once per page. Never touched:
fenced and indented code, inline code, headings, existing links and images, raw
HTML, math, URLs, and a page whose own title names the term. Sources are never
rewritten. Folder indexes, table rows and a term in parentheses right after its own
expansion, `(GPU)`, are left alone too.
"""
import re

GLOSSARY = "references/glossary.md"
SECTION = re.compile(r"^## +(\S.*?)\s*$", re.M)
FENCE = re.compile(r"^\s*(```|~~~)")
MASK = re.compile(
    r"`[^`\n]*`"                                   # inline code
    r"|!?\[[^\]\n]*\]\([^)\n]*\)"                  # links and images
    r"|\[[^\]\n]*\]\[[^\]\n]*\]"                   # reference links
    r"|<[^>\n]+>"                                  # raw HTML tags
    r"|https?://[^\s)>\]]+"                        # bare URLs
    r"|\$[^$\n]+\$"                                # inline math
)


def slug(term):
    return re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")


def plain(text):
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[*_`]", "", text).strip()


def parse(text):
    """{term: tooltip} from the glossary source: the bold expansion, else the first sentence."""
    terms = {}
    parts = SECTION.split(text)
    for i in range(1, len(parts) - 1, 2):
        term, body = parts[i].strip(), parts[i + 1].strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9+-]{1,15}", term):
            continue
        m = re.match(r"\*\*(.+?)\.?\*\*", body)
        tip = plain(m.group(1)) if m else plain(body.split(". ")[0])
        terms[term] = tip.replace('"', "'")
    return terms


def link_terms(page, text, terms):
    """`text` with the first use of each term linked. Returns (text, number of links)."""
    if not terms or page == GLOSSARY:
        return text, 0
    if re.search(r"^## +Contents\b", text, re.M):   # a folder index: tables of page descriptions, not prose
        return text, 0
    h1 = re.search(r"^# +(.+?)\s*#*\s*$", text, re.M)
    title = h1.group(1) if h1 else ""
    todo = {t: re.compile(r"(?<![\w./#-])" + re.escape(t) + r"(?![\w-])") for t in terms
            if not re.search(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", title)}
    lines = text.split("\n")
    fence, count = False, 0
    for n, line in enumerate(lines):
        if FENCE.match(line):
            fence = not fence
            continue
        if fence or not todo or not line.strip() or line.startswith(("#", "    ", "\t", "<", "$$", ":::", "[!", "|")):
            continue
        # work on the line with everything we must not touch blanked out, then splice the links in
        masked = MASK.sub(lambda m: "\0" * len(m.group(0)), line)
        edits = []
        for t, rx in list(todo.items()):
            m = next((x for x in rx.finditer(masked) if not (x.start() and masked[x.start() - 1] == "(" and masked[x.end():x.end() + 1] == ")")), None)  # "(GPU)" is the page defining it
            if m:
                edits.append((m.start(), m.end(), t))
                del todo[t]
        if not edits:
            continue
        edits.sort()
        out, last = [], 0
        for a, b, t in edits:
            if a < last:           # overlaps an earlier edit: leave it for no page rather than corrupt the line
                continue
            out += [line[last:a], '[%s](/references/glossary?id=%s "%s")' % (t, slug(t), terms[t])]
            last = b
            count += 1
        lines[n] = "".join(out) + line[last:]
    return "\n".join(lines), count
