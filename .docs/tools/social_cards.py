#!/usr/bin/env python3
"""Link-preview pictures ("social cards") for the share pages of the staged site.

Each content page gets a 1200x630 PNG with the site name, the page's folder, its
title and its summary, written next to its share page (`<page>/card.png`) and used
as that page's `og:image`. Without Pillow no card is made and the share pages keep
the site icon.

Used by share_pages.py; the staged copy only.
"""
import io
import os

W, H = 1200, 630
BG, ACCENT, TEXT, MUTED = (31, 122, 82), (244, 236, 216), (255, 255, 255), (214, 236, 224)
BOLD_FONTS = ("DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial Bold.ttf")
BOOK_FONTS = ("DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf")
FONT_DIRS = ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation",
             "/usr/share/fonts/dejavu", "/Library/Fonts", "/System/Library/Fonts/Supplemental",
             "C:\\Windows\\Fonts")


def have_pillow():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def font(names, size):
    from PIL import ImageFont
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except OSError:
                    pass
    return ImageFont.load_default(size)  # Pillow's built-in scalable font


def wrap(draw, text, fnt, width, max_lines):
    """Words wrapped to `width` pixels, at most `max_lines` lines (the last one ends with an ellipsis)."""
    lines, cur = [], ""
    words = text.split()
    for i, w in enumerate(words):
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= width or not cur:
            cur = trial
            continue
        lines.append(cur)
        cur = w
        if len(lines) == max_lines:
            break
    else:
        lines.append(cur)
    if len(lines) > max_lines or (len(lines) == max_lines and " ".join(lines) != " ".join(words)):
        lines = lines[:max_lines]
        last = lines[-1].rstrip(" .,;:")
        while last and draw.textlength(last + "\u2026", font=fnt) > width:
            last = last[:-1].rstrip()
        lines[-1] = last + "\u2026"
    return lines


def card_bytes(title, desc="", kicker="", site="aCupOfTea"):
    """PNG bytes of one card."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, H - 14, W, H], fill=ACCENT)
    pad, width = 72, W - 144
    d.text((pad, 56), site, font=font(BOLD_FONTS, 34), fill=ACCENT)
    if kicker:
        d.text((pad, 108), kicker, font=font(BOOK_FONTS, 28), fill=MUTED)
    tf = font(BOLD_FONTS, 68)
    y = 190
    for line in wrap(d, title, tf, width, 3):
        d.text((pad, y), line, font=tf, fill=TEXT)
        y += 84
    if desc:
        df = font(BOOK_FONTS, 32)
        y += 18
        for line in wrap(d, desc, df, width, 3 if y < 380 else 2):
            d.text((pad, y), line, font=df, fill=MUTED)
            y += 44
    buf = io.BytesIO()
    im = im.quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)  # flat colours + text: a third of the size
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def write_card(path, title, desc="", kicker=""):
    """Write one card to `path`; False when it could not be made (no Pillow, unusual text)."""
    if not have_pillow():
        return False
    try:
        data = card_bytes(title, desc, kicker)
    except Exception:  # a broken font or odd text must not stop the build
        return False
    with open(path, "wb") as f:
        f.write(data)
    return True
