"""One reading of a Markdown page, shared by the generators.

`Page` parses a page once: its front matter (PyYAML), the first `# ` heading,
and the menu label rules. The sidebar generator (gen_sidebar.py) uses it; the
other tools can build on it instead of each re-reading pages with their own
rules. Behaviour matches what gen_sidebar.sh did, so the menu does not change.
"""
import os
import re

import yaml

from common import DupKeyLoader, split_front_matter


def title_case_words(name):
    """'hpc_storage' -> 'Hpc Storage' (first letter of each word upper-cased, the rest kept)."""
    return " ".join(w[:1].upper() + w[1:] for w in re.sub(r"[-_]", " ", name).split())


def label_after_last_hyphen(h1):
    """Page label from a heading: the text after the last hyphen (the whole heading without one)."""
    return (h1.rsplit("-", 1)[-1] if "-" in h1 else h1).strip()


def group_before_last_hyphen(h1):
    """Folder group name from a README heading: the text before the last hyphen."""
    return (h1.rsplit("-", 1)[0] if "-" in h1 else h1).strip()


class Page:
    """A page read from `path` (repo-relative `rel` for messages)."""

    def __init__(self, path, rel=None):
        self.path = path
        self.rel = rel or path
        with open(path, encoding="utf-8", errors="replace", newline="") as f:
            self.text = f.read()
        self.front, self.body = self._front_matter(self.text)
        self.h1 = self._first_h1(self.body)

    @staticmethod
    def _front_matter(text):
        """(front matter dict, body text); a page without usable front matter has {}."""
        try:
            split = split_front_matter(text)
        except ValueError:
            return {}, text
        if split is None:
            return {}, text
        yaml_text, offset = split
        try:
            data = yaml.load(yaml_text, Loader=DupKeyLoader)
        except yaml.YAMLError:
            data = None
        return (data if isinstance(data, dict) else {}), text[offset:]

    @staticmethod
    def _first_h1(body):
        for line in body.splitlines():
            if line.startswith("# "):
                return line[2:]
        return ""

    def field(self, key):
        """A front matter value as one line of text; '' when absent or not a plain value."""
        v = self.front.get(key)
        if v is None or isinstance(v, (dict, list)):
            return ""
        return str(v).strip()

    @property
    def order(self):
        """Reading position (a whole number), or None."""
        v = self.front.get("order")
        return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else None

    def menu_label(self):
        """This page's own entry in the menu: sidebar_label, else the heading's last-hyphen part,
        else the file name in words."""
        lab = self.field("sidebar_label")
        if lab:
            return lab
        title = label_after_last_hyphen(self.h1) if self.h1 else ""
        return title or title_case_words(os.path.basename(self.path)[:-3])

    def menu_group(self, folder_name):
        """A folder README's group name: sidebar_group, else the heading before its last hyphen,
        else the folder name in words."""
        g = self.field("sidebar_group")
        if g:
            return g
        name = group_before_last_hyphen(self.h1) if self.h1 else ""
        return name or title_case_words(folder_name)
