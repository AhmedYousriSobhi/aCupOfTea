#!/usr/bin/env python3
"""sitemap.xml, feed.xml (Atom) and robots.txt for the staged site.

  sitemap.xml  the site root and every content page at its share-page address
               (`<base>fields/x/page/`), with the date of its last git commit.
  feed.xml     the newest pages added (the same git-history data as "Recently
               added"), each with its title and summary, for feed readers.
  robots.txt   allows everything and names the sitemap.

Used by stage_site.py; the staged copy only. Dates are `YYYY-MM-DD` (git, UTC-ish);
without git history the sitemap has no `lastmod` and the feed has no entries.
"""
import html
import os
from urllib.parse import quote

import share_pages

SITE_TITLE = "aCupOfTea"
SITE_SUBTITLE = "Knowledge, served in short sips."


def page_url(base, page):
    d = share_pages.share_dir(page)
    return base if d is None else base + quote(d, safe="/") + "/"


def sitemap(base, pages, dates):
    """XML text; `pages` are the content pages (the home page is added first)."""
    urls = [(base, dates.get("README.md"))]
    for p in pages:
        if share_pages.share_dir(p) is not None:
            urls.append((page_url(base, p), dates.get(p)))
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, day in urls:
        out.append("  <url><loc>%s</loc>%s</url>" % (html.escape(loc), "<lastmod>%s</lastmod>" % day if day else ""))
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def atom(base, entries):
    """Atom feed from [(YYYY-MM-DD, page, title, summary)], newest first."""
    updated = entries[0][0] if entries else "1970-01-01"
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom">',
           "  <title>%s</title>" % html.escape(SITE_TITLE), "  <subtitle>%s</subtitle>" % html.escape(SITE_SUBTITLE),
           '  <link href="%s"/>' % html.escape(base), '  <link rel="self" href="%sfeed.xml"/>' % html.escape(base),
           "  <id>%s</id>" % html.escape(base), "  <updated>%sT00:00:00Z</updated>" % updated]
    for day, page, title, summary in entries:
        url = page_url(base, page)
        out += ["  <entry>", "    <title>%s</title>" % html.escape(title),
                '    <link href="%s"/>' % html.escape(url), "    <id>%s</id>" % html.escape(url),
                "    <updated>%sT00:00:00Z</updated>" % day]
        if summary:
            out.append("    <summary>%s</summary>" % html.escape(summary))
        out.append("  </entry>")
    out.append("</feed>")
    return "\n".join(out) + "\n"


def robots(base):
    return "User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % base


def write_all(out, base, pages, dates, recent, sources):
    """Write the three files. `recent` is [(day, page)]; `sources` {page: original text} for titles and summaries."""
    if not base.endswith("/"):
        base += "/"
    entries = []
    for day, page in recent:
        title, desc = share_pages.page_meta(sources.get(page, ""))
        entries.append((day, page, title or os.path.basename(page)[:-3], desc))
    files = {"sitemap.xml": sitemap(base, pages, dates), "feed.xml": atom(base, entries), "robots.txt": robots(base)}
    for name, text in files.items():
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    return len(pages), len(entries)
