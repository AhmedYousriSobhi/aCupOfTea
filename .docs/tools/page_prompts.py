"""The questions new_page.py asks (folder, tags, kind, domains, relations) and how an
answer is checked. Part of new_page.py (split for size); page_gui.py reuses it.
"""
import argparse
import difflib
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import page_scaffold as sc  # noqa: E402
from page_scaffold import *  # noqa: F401,F403,E402


# ---------- prompts ----------

class Invalid(Exception):
    """A bad answer; the message says what is wrong."""


def resolve(ask, supplied, parse, prompt):
    """Get an answer and parse it. A bad option exits; a bad typed answer is asked again,
    so one typo does not throw away everything already answered."""
    if supplied is not None:
        try:
            return parse(supplied)
        except Invalid as e:
            sys.exit("error: %s" % e)
    while True:
        try:
            return parse(prompt())
        except Invalid as e:
            if not ask.interactive or ask.yes:
                sys.exit("error: %s" % e)
            print("  %s; try again" % e)


class Asker:
    def __init__(self, yes):
        self.yes = yes
        self.interactive = sys.stdin.isatty()

    def text(self, prompt, default="", required=True):
        if self.yes or not self.interactive:
            if default or not required:
                return default
            sys.exit("error: %s is required (pass it as an option)" % prompt.split(" (")[0].lower())
        hint = " [%s]" % default if default else ""
        value = input("%s%s: " % (prompt, hint)).strip()
        return value or default

    def confirm(self, prompt, default=True):
        if self.yes or not self.interactive:
            return default
        hint = "[Y/n]" if default else "[y/N]"
        value = input("%s %s " % (prompt, hint)).strip().lower()
        return default if not value else value.startswith("y")


def complete_with(options):
    try:
        import readline
    except ImportError:
        return
    def completer(text, state):
        head, _, last = text.rpartition(",")
        last = last.lstrip()
        hits = [o for o in options if o.startswith(last)]
        prefix = (head + ", ") if head else ""
        return prefix + hits[state] if state < len(hits) else None
    readline.set_completer_delims("")
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")


# ---------- steps ----------

def page_words(rel, h1):
    return words(sidebar_label(h1)) | words(os.path.basename(rel)[:-3])


def suggest_folders(title, folders, limit=5):
    """Rank folders by title words found in their path and page titles.

    Rare words count more than common ones ("slurm" beats "job"), so a folder
    full of matching pages wins over one that only shares a generic word.
    """
    want = words(title)
    bags = {}
    for folder, pages in folders.items():
        path = words(folder.replace("/", " "))
        hits = {}
        for rel, h1 in pages:
            found = page_words(rel, h1) | words(h1)
            if os.path.basename(rel) == "README.md":
                found |= words(read(os.path.join(sc.ROOT, rel)))   # the folder's own description
            for w in found:
                hits[w] = hits.get(w, 0) + 1
        bags[folder] = (path, hits)
    df = {w: sum(1 for path, hits in bags.values() if w in path or w in hits) for w in want}
    scored = []
    for folder, (path, hits) in bags.items():
        score = sum(math.log((1 + len(bags)) / (1 + df[w])) * (2 * (w in path) + min(3, hits.get(w, 0)))
                    for w in want)
        if score > 0:
            scored.append((-score, folder.count("/"), folder))
    return [f for _, _, f in sorted(scored)[:limit]]


def folder_problem(folder, folders):
    if not folder:
        return "no folder chosen"
    if folder.startswith("/") or "\\" in folder or any(part in ("", ".", "..") for part in folder.split("/")):
        return "%s is not a plain folder path inside the repository (no .., . or empty parts)" % folder
    if folder.split("/")[0] not in {f.split("/")[0] for f in folders}:
        return "%s is not under an existing top-level folder" % folder
    bad = [p for p in folder.split("/") if p != slug(p)]
    if bad and not os.path.isdir(os.path.join(sc.ROOT, folder)):
        return "new folder names must be lowercase-kebab-case: %s" % ", ".join(bad)
    return ""


def pick(options, answer):
    if answer.isdigit() and 0 < int(answer) <= len(options):
        return options[int(answer) - 1]
    return answer.strip().strip("/")


def subfolders(folder, folders):
    depth = folder.count("/") + 1
    return sorted({"/".join(f.split("/")[:depth + 1]) for f in folders
                   if f.startswith(folder + "/")})


def choose_folder(args, ask, title, folders):
    if args.folder:
        folder = args.folder.strip("/")
        problem = folder_problem(folder, folders)
        if problem:
            sys.exit("error: " + problem)
    else:
        hits = suggest_folders(title, folders)
        options = hits or sorted({f.split("/")[0] for f in folders})
        print("\nWhere does it go?" + ("  (closest folders first)" if hits else ""))
        for i, f in enumerate(options, 1):
            print("  %d) %s" % (i, f))
        print("  or type a folder path (Tab completes)")
        while True:
            complete_with(sorted(folders))
            folder = pick(options, ask.text("Folder", "1" if hits and ask.yes else ""))
            problem = folder_problem(folder, folders)
            if not problem:
                break
            if not ask.interactive or ask.yes:
                sys.exit("error: " + problem)
            print("  " + problem + ", try again")
        # Offer to go deeper when the chosen folder has subfolders.
        while not ask.yes and subfolders(folder, folders):
            children = subfolders(folder, folders)
            print("\n%s has subfolders:" % folder)
            print("  0) put it here")
            for i, f in enumerate(children, 1):
                print("  %d) %s" % (i, f))
            answer = ask.text("Choice", "0")
            if answer == "0":
                break
            choice = pick(children, answer)
            if folder_problem(choice, folders):
                print("  not a valid choice, try again")
                continue
            folder = choice
    if not os.path.isdir(os.path.join(sc.ROOT, folder)):
        if not ask.confirm("%s does not exist. Create it?" % folder, default=bool(getattr(args, "create_folder", False))):
            sys.exit("Stopped: no folder created.")
    return folder


def similar_pages(title, folders):
    """[(rel, h1)] of existing pages that look like the same topic, best first (at most 3)."""
    want = words(title)
    norm = slug(title)
    hits = []
    for pages in folders.values():
        for rel, h1 in pages:
            if os.path.basename(rel) == "README.md":
                continue
            have = page_words(rel, h1)
            covered = len(want & have) / max(1, len(want))
            jaccard = len(want & have) / max(1, len(want | have))
            ratio = max(difflib.SequenceMatcher(None, norm, slug(sidebar_label(h1))).ratio(),
                        difflib.SequenceMatcher(None, norm, os.path.basename(rel)[:-3]).ratio())
            score = max(jaccard, ratio, covered if len(want) >= 2 else 0)
            if jaccard >= 0.5 or ratio >= 0.8 or (len(want) >= 2 and covered >= 0.75):
                hits.append((-score, rel, h1))
    return [(rel, h1) for _, rel, h1 in sorted(hits)[:3]]


def warn_similar(title, folders, ask):
    hits = similar_pages(title, folders)
    if not hits:
        return
    print("\nSimilar pages already exist:")
    for rel, h1 in hits:
        print("  - %s  \"%s\"" % (rel, h1))
    if not ask.confirm("Continue with a new page?"):
        sys.exit("Stopped: nothing created.")


def numeronym(short, word):
    """k8s ~ kubernetes, i18n ~ internationalization."""
    m = re.fullmatch(r"([a-z])(\d+)([a-z])", short)
    return bool(m) and len(word) == int(m.group(2)) + 2 and word[0] == m.group(1) and word[-1] == m.group(3)


def near_word(word, pools):
    """The word from `pools` (lists, most trusted first) that `word` is a short form or a typo of, or ""."""
    best = None
    for rank, pool in enumerate(pools):
        for cand in pool:
            if cand == word or len(cand) < 3:
                continue
            score = 1.0 if numeronym(word, cand) else difflib.SequenceMatcher(None, word, cand).ratio()
            if score >= 0.75 and (best is None or (score, -rank) > best[0]):
                best = ((score, -rank), cand)
    return best[1] if best else ""


def choose_tags(args, ask, title, known, default=None):
    def prompt():
        want = words(title)
        hint = [k for k, label in sorted(known.items()) if want & (words(k) | words(label))]
        print("\nTags (comma separated, Tab completes). Known: %s" % ", ".join(sorted(known)))
        complete_with(sorted(known))
        return ask.text("Tags", default if default is not None else ", ".join(hint), required=False)

    def parse(raw):
        out = []
        for t in ([] if raw.strip() == "-" else raw.split(",")):
            t = slug(t)
            if t and t not in out:
                out.append(t)
        if len(out) > MAX_TAGS:
            raise Invalid("at most %d tags per page" % MAX_TAGS)
        return out

    tags = resolve(ask, args.tags, parse, prompt)
    new = {}
    wanted = dict(getattr(args, "new_tag", None) or [])
    title_words = [w for w in re.findall(r"[a-z0-9]+", title.lower())]
    for t in [t for t in tags if t not in known]:
        # a new tag that looks like a known one (or a word of the title) is usually a typo or a short form;
        # one confirmed with --new-tag is taken as meant
        guess = "" if t in wanted else near_word(t, [sorted(known), title_words])
        if guess:
            if ask.interactive and not ask.yes and ask.confirm('"%s" looks like "%s". Use that instead?' % (t, guess)):
                tags[tags.index(t)] = guess
                t = guess
                if t in known:
                    continue
            else:
                print("Note: \"%s\" looks like \"%s\"; check it is not a typo." % (t, guess))
        label = wanted.get(t) or " ".join(w.capitalize() for w in t.split("-"))
        print("\"%s\" is a new tag (label \"%s\")." % (t, label))
        if t in wanted or ask.confirm("Add it to the tag list?", default=False):
            new[t] = label
        else:
            tags.remove(t)
    tags = list(dict.fromkeys(tags))
    return tags, new


def split_list(raw):
    """Comma (or space) separated answer as a list, without blanks or repeats."""
    out = []
    for x in re.split(r"[,\s]+", raw):
        if x and x not in out:
            out.append(x)
    return out


def closest(word, allowed):
    """The allowed value a typo or short form most likely means ("hpc" -> systems-and-hpc), or ""."""
    word = slug(word)
    for a in allowed:
        if word in a.split("-"):
            return a
    near = difflib.get_close_matches(word, allowed, n=1, cutoff=0.7)
    return near[0] if near else ""


def choose_list(label, raw, allowed, limit):
    out = split_list(raw)
    bad = [x for x in out if x not in allowed]
    if bad:
        hints = ["%s (did you mean %s?)" % (x, closest(x, allowed)) if closest(x, allowed) else x for x in bad]
        raise Invalid("unknown %s %s; allowed: %s" % (label, ", ".join(hints), ", ".join(allowed)))
    if len(out) > limit:
        raise Invalid("at most %d %s per page" % (limit, label))
    return out


def choose_type(args, ask, folder, folders, default=None):
    """One or two kinds, the main one first. Returns (types, new_types); a kind that is not in the
    taxonomy can be added (a new_types entry is key -> description)."""
    types = load_section("types")
    new = {}
    for key, description in (getattr(args, "new_type", None) or []):
        new[key] = description

    def prompt():
        near = neighbours(folder, folders, "type")
        print("\nKind of page, one or two comma separated (the main one first): %s" % ", ".join(types + list(new)))
        print("  concept explains an idea, guide shows how to do something, reference is for looking up,")
        print("  note is a short write-up, problem/project/experiment describe work.")
        print("  None fits? Type a new kind and you will be asked to add it.")
        complete_with(types + list(new))
        return ask.text("Type", default if default is not None else (near[0] if near else "concept"))

    can_ask = args.type is None and ask.interactive and not ask.yes

    def parse(raw):
        known = types + list(new)
        out = []
        for x in ([] if raw.strip() == "-" else split_list(raw)):
            if x not in known and can_ask:
                guess, key = closest(x, known), slug(x)
                if guess and ask.confirm("Unknown kind \"%s\". Use %s?" % (x, guess)):
                    x = guess
                elif key and ask.confirm("Add \"%s\" as a new kind of page?" % key, default=False):
                    description = ""
                    while not description:
                        description = ask.text("One line: what is this kind of page?")
                    new[key] = description
                    x = key
            if x not in out:
                out.append(x)
        return choose_list("type", ", ".join(out), types + list(new), MAX_TYPES)

    return resolve(ask, args.type, parse, prompt), new


def guess_domains(title, folder):
    """Domains whose description shares words with the title or folder path."""
    want = words(title) | words(folder.replace("/", " ").replace("-", " "))
    want -= {"field", "concept", "tool"}
    scored = sorted((-len(want & w), d) for d, w in domain_words().items() if want & w)
    return [d for n, d in scored if n == scored[0][0]]   # only the best match(es)


def default_domains(folder, folders, title):
    """Subjects suggested for a page: the folder's usual ones, else the folder default, else a guess."""
    near = neighbours(folder, folders, "domains")
    if not near:
        near = next((v for k, v in sorted(folder_defaults().items(), key=lambda kv: -len(kv[0]))
                     if folder == k or folder.startswith(k + "/")), [])
    return near or guess_domains(title, folder)


def choose_domains(args, ask, folder, folders, title, default=None):
    """One to three related subjects. Returns (domains, new_domains); an unknown subject is matched to a
    known one ("hpc" -> systems-and-hpc) or, when typed in answer to the question, can be added."""
    domains = load_section("domains")
    new = {}

    def prompt():
        near = default_domains(folder, folders, title)
        print("\nSubjects (domains) put the page in Explore by subject; up to %d related ones, comma separated." % MAX_DOMAINS)
        print("Known: %s" % ", ".join(domains + list(new)))
        complete_with(domains + list(new))
        return ask.text("Domains", default if default is not None else ", ".join(near[:MAX_DOMAINS]), required=False)

    can_ask = args.domains is None and ask.interactive and not ask.yes
    for key, description in (getattr(args, "new_domain", None) or []):
        new[key] = (" ".join(w.capitalize() for w in key.split("-")), description)

    def parse(raw):
        known = domains + list(new)
        out = []
        for x in ([] if raw.strip() == "-" else split_list(raw)):
            if x not in known and can_ask:
                guess = closest(x, known)
                key = slug(x)
                label = " ".join(w.capitalize() for w in key.split("-"))
                if guess and ask.confirm("Unknown subject \"%s\". Use %s?" % (x, guess)):
                    x = guess
                elif key and ask.confirm("Add \"%s\" (label \"%s\") as a new subject?" % (key, label), default=False):
                    description = ""
                    while not description:
                        description = ask.text("One line describing it")
                    new[key] = (label, description)
                    x = key
            if x not in out:
                out.append(x)
        chosen = choose_list("domains", ", ".join(out), domains + list(new), MAX_DOMAINS)
        pairs = unrelated_pairs(chosen, new)
        if pairs:
            text = "; ".join("%s and %s" % p for p in pairs) + (" are" if len(pairs) > 1 else " is") + \
                " not marked as related in taxonomy.yaml (a page usually belongs to one area)"
            if can_ask:
                print("  " + text)
                if not ask.confirm("Keep these subjects together anyway?", default=True):
                    raise Invalid("choose subjects that go together")
            else:
                print("Note: " + text + ".")
        return chosen

    return resolve(ask, args.domains, parse, prompt), new


def page_ids(raw, ids, role):
    out = split_list(raw)
    unknown = [r for r in out if r not in ids]
    if unknown:
        hints = ["%s (did you mean %s?)" % (r, closest(r, sorted(ids))) if closest(r, sorted(ids)) else r
                 for r in unknown]
        raise Invalid("no page has the id %s; only pages with an id in their front matter can be %s"
                      % (", ".join(hints), role))
    return out


def ask_metadata(args, ask, title, folder, folders, have=()):
    """The questions every page gets: type, subjects, tags, level, prerequisites, related.
    Fields named in `have` (already in the page's front matter) are not asked."""
    types, new_types = ([], {}) if "type" in have else choose_type(args, ask, folder, folders)
    domains, new_domains = ([], {}) if "domains" in have else choose_domains(args, ask, folder, folders, title)
    tags, new_tags = ([], {}) if "tags" in have else choose_tags(args, ask, title, load_tags())

    def parse_level(raw):
        raw = raw.strip().lower()
        if raw and raw not in LEVELS:
            raise Invalid("level must be one of %s" % ", ".join(LEVELS))
        return raw
    level = "" if "level" in have else resolve(
        ask, args.level, parse_level, lambda: ask.text("Level (%s, optional)" % "/".join(LEVELS), required=False))
    ids = existing_ids(folders)

    def ask_ids(heading, label):
        def prompt():
            print("\n%s: ids of pages to %s (comma separated, Tab completes)." % (heading, label))
            complete_with(sorted(ids))
            return ask.text(heading, required=False)
        return prompt
    if "relations" in have:
        prereqs, related = [], []
    else:
        prereqs = resolve(ask, args.prerequisites, lambda raw: page_ids(raw, ids, "a prerequisite"),
                          ask_ids("Prerequisites", "read first"))
        related = [r for r in resolve(ask, args.related, lambda raw: page_ids(raw, ids, "related"),
                                      ask_ids("Related", "see also")) if r not in prereqs]
    return {"types": types, "new_types": new_types, "domains": domains, "new_domains": new_domains, "tags": tags,
            "new_tags": new_tags, "level": level, "prereqs": prereqs, "related": related, "ids": ids}
