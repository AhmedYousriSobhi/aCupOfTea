#!/usr/bin/env python3
"""Losslessly recompress the PNG and JPEG images of the staged site.

Called by stage_site.py on the staging copy only; repository images are never
touched. Each image is re-saved with Pillow (`optimize=True`; JPEG with
`quality="keep"`), then decoded again and compared with the original: the new
file replaces the old one only when it is smaller AND has the same size, mode
and pixels. So the result is lossless by check, not by assumption (a JPEG
re-encode is rarely pixel-identical, so most JPEGs stay as they are).

Without Pillow the step is skipped with a message, so local runs still work.

Usage: python3 .docs/tools/optimize_images.py DIR   (rewrites images in DIR)
"""
import io
import os
import sys
from concurrent.futures import ProcessPoolExecutor

EXTS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG"}
KEEP_INFO = ("transparency", "icc_profile", "dpi", "gamma", "exif")


def _pixels(im):
    return im.size, im.mode, im.getpalette() if im.mode == "P" else None, im.tobytes()


def optimize_one(path):
    """Recompress one file in place if that is smaller and lossless. Returns (before, after)."""
    from PIL import Image

    before = os.path.getsize(path)
    try:
        with open(path, "rb") as f:
            data = f.read()
        im = Image.open(io.BytesIO(data))
        fmt = im.format
        if fmt not in ("PNG", "JPEG") or getattr(im, "n_frames", 1) > 1:
            return before, before
        im.load()
        kwargs = {k: im.info[k] for k in KEEP_INFO if k in im.info}
        if fmt == "JPEG":
            kwargs.update(quality="keep", subsampling="keep", qtables="keep")
            if im.info.get("progressive"):
                kwargs["progressive"] = True
        buf = io.BytesIO()
        im.save(buf, fmt, optimize=True, **kwargs)
        new = buf.getvalue()
        if len(new) >= before:
            return before, before
        if _pixels(Image.open(io.BytesIO(new))) != _pixels(im):
            return before, before
    except Exception:  # unreadable or unusual file: leave it as it is
        return before, before
    with open(path, "wb") as f:
        f.write(new)
    return before, len(new)


def find_images(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for n in filenames:
            if os.path.splitext(n)[1].lower() in EXTS:
                yield os.path.join(dirpath, n)


def optimize_tree(root):
    """Recompress every PNG/JPEG under root. Returns a one-line summary."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        return "images: skipped (Pillow not installed)"
    paths = sorted(find_images(root))
    if not paths:
        return "images: none found"
    with ProcessPoolExecutor() as pool:
        results = list(pool.map(optimize_one, paths, chunksize=8))
    changed = sum(1 for b, a in results if a < b)
    before = sum(b for b, _ in results)
    after = sum(a for _, a in results)
    mb = 1024 * 1024
    return (f"images: {changed} of {len(paths)} recompressed, "
            f"{before / mb:.1f} MB -> {after / mb:.1f} MB")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.splitlines()[-1])
    print(optimize_tree(sys.argv[1]))
