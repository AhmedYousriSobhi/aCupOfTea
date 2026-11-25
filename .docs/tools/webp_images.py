#!/usr/bin/env python3
"""WebP copies of the PNG images and image sizes, in the staged site only.

Called by stage_site.py on the staging copy; repository files are never touched.

1. Each PNG gets a lossless `.webp` next to it. It is kept only when it is smaller
   AND decodes to exactly the same pixels (checked, not assumed). The PNG stays
   in the output, so anything that still points at it (a link preview, a
   notebook page) keeps working.
2. In every staged page, a Markdown image that points at a local PNG, JPEG or
   WebP file is rewritten: a PNG with a WebP copy now points at the copy, and
   the image gets its width and height (Docsify's `':size=WxH'` option), so the
   page no longer jumps when the picture arrives. Images that already have a
   title, fenced code, and remote or data addresses are left alone.

Without Pillow both steps are skipped with a message.

Usage: python3 .docs/tools/webp_images.py DIR
"""
import io
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from urllib.parse import unquote

SKIP_DIRS = {".git", "icons"}   # icons: the site's own logo and favicon files are referenced by name
IMAGE = re.compile(r"!\[([^\]\n]*)\]\(\s*([^()\s'\"<>]+)\s*\)")
IMG_SRC = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]+\.png)(")', re.I)
FENCE = re.compile(r"(^```.*?^```[^\n]*$|^~~~.*?^~~~[^\n]*$)", re.S | re.M)
SIZED = {".png", ".jpg", ".jpeg", ".webp"}


def _pixels(im):
    im = im.convert("RGBA")
    return im.size, im.tobytes()


def convert_one(path):
    """Write path[:-4] + '.webp' when lossless and smaller. Returns (png bytes, webp bytes or 0)."""
    from PIL import Image
    before = os.path.getsize(path)
    try:
        im = Image.open(path)
        if getattr(im, "n_frames", 1) > 1:
            return before, 0
        im.load()
        buf = io.BytesIO()
        im.save(buf, "WEBP", lossless=True, quality=100, method=4)
        data = buf.getvalue()
        if len(data) >= before or _pixels(Image.open(io.BytesIO(data))) != _pixels(im):
            return before, 0
    except Exception:  # unreadable or unusual file: keep the PNG only
        return before, 0
    with open(path[:-4] + ".webp", "wb") as f:
        f.write(data)
    return before, len(data)


def find(root, ext):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for n in filenames:
            if n.lower().endswith(ext):
                yield os.path.join(dirpath, n)


def size_of(path, cache):
    if path not in cache:
        try:
            from PIL import Image
            with Image.open(path) as im:
                cache[path] = im.size
        except Exception:
            cache[path] = None
    return cache[path]


def rewrite_text(text, page_dir, root, sizes):
    """Markdown with local images pointing at WebP where it exists, with sizes. Returns (text, changed)."""
    changed = [0]

    def local(src):
        if re.match(r"^[a-z][a-z0-9+.-]*:|^//|^#", src, re.I):
            return None
        rel = unquote(src.split("?")[0].split("#")[0])
        full = os.path.normpath(os.path.join(root if rel.startswith("/") else page_dir, rel.lstrip("/")))
        return full if full.startswith(root) else None

    def image(m):
        alt, src = m.group(1), m.group(2)
        full = local(src)
        if not full or os.path.splitext(full)[1].lower() not in SIZED:
            return m.group(0)
        if full.lower().endswith(".png") and os.path.isfile(full[:-4] + ".webp"):
            full, src = full[:-4] + ".webp", src[:-4] + ".webp"
        if not os.path.isfile(full):
            return m.group(0)
        wh = size_of(full, sizes)
        changed[0] += 1
        return "![%s](%s%s)" % (alt, src, " ':size=%dx%d'" % wh if wh else "")

    def html(m):
        full = local(m.group(2))
        if full and os.path.isfile(full[:-4] + ".webp"):
            changed[0] += 1
            return m.group(1) + m.group(2)[:-4] + ".webp" + m.group(3)
        return m.group(0)

    parts = FENCE.split(text)
    for i in range(0, len(parts), 2):  # odd parts are the fenced blocks
        parts[i] = IMG_SRC.sub(html, IMAGE.sub(image, parts[i]))
    return "".join(parts), changed[0]


def convert_tree(root):
    """WebP copies and rewritten pages under root. Returns a one-line summary."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        return "webp: skipped (Pillow not installed)"
    root = os.path.abspath(root)
    pngs = sorted(find(root, ".png"))
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(convert_one, pngs, chunksize=8))
    made = [(b, w) for b, w in results if w]
    sizes, pages, refs = {}, 0, 0
    for path in find(root, ".md"):
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        new, n = rewrite_text(text, os.path.dirname(path), root, sizes)
        if n:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            pages += 1
            refs += n
    mb = 1024 * 1024
    return (f"webp: {len(made)} of {len(pngs)} PNGs have a smaller lossless copy "
            f"({sum(b for b, _ in made) / mb:.1f} MB -> {sum(w for _, w in made) / mb:.1f} MB); "
            f"{refs} image links in {pages} pages updated")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.splitlines()[-1])
    print(convert_tree(sys.argv[1]))
