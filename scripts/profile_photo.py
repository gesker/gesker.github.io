#!/usr/bin/env python3
"""Regenerate every profile-photo derivative from one source image.

The photo appears in five places and they must stay one face: the site avatar,
the Open Graph card, the LinkedIn photo, the LinkedIn banner, and the master
portrait. Swapping the source and re-running this is the only correct way to
change it -- cropping by hand guarantees one surface drifts.

LinkedIn profile photos cannot be fetched from a URL: the page 301s to a login
wall and the image itself sits on a signed media.licdn.com URL that only exists
inside an authenticated session. Save the file yourself, then:

    just profile-photo                       # uses the default source path
    just profile-photo path/to/photo.jpg     # or name it

Usage:
    python3 scripts/profile_photo.py [SOURCE] [--top 0.12]
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

MASTER = "src/images/profile_picture.jpg"
AVATAR = "src/images/profile_picture_avatar.jpg"
OG_CARD = "src/images/og-card.jpg"
LI_PHOTO = "documentation/linkedin/linkedin-photo.jpg"
LI_BANNER = "documentation/linkedin/linkedin-banner.jpg"

# Where the source is looked for, in order, when no path is given.
CANDIDATES = (
    "documentation/linkedin/profile-source.jpg",
    "documentation/linkedin/profile-source.png",
    "src/images/profile_picture_source.jpg",
    "src/images/profile_picture_source.png",
)

BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
REG = "/System/Library/Fonts/Supplemental/Arial.ttf"

BASE = (30, 30, 46)          # catppuccin mocha base, matches the site
ACCENT = (198, 160, 246)     # mauve
INK = (245, 245, 250)
SOFT = (205, 214, 244)
MUTED = (166, 173, 200)
MONO = (49, 50, 68)

MIN_SOURCE = 400  # below this the avatar is mush at 2x

# Pillow exposes LANCZOS at the top level and under Image.Resampling; the
# type stubs only know one of them, and only one is guaranteed at runtime.
RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def square(im, top_fraction):
    """Centre horizontally, honour a vertical offset (faces sit high)."""
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = int(h * top_fraction)
    top = max(0, min(top, h - side))
    return im.crop((left, top, left + side, top + side))


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    top = float(argv[argv.index("--top") + 1]) if "--top" in argv else 0.12

    source = args[0] if args else next((c for c in CANDIDATES if os.path.exists(c)), None)
    if not source or not os.path.exists(source):
        sys.exit(
            "no source photo.\n"
            "  Save your LinkedIn photo, then run:  just profile-photo <path>\n"
            "  Expected default: " + CANDIDATES[0]
        )

    im = Image.open(source).convert("RGB")
    allow_small = "--allow-small" in argv
    short = min(im.size)
    if short < MIN_SOURCE and not allow_small:
        sys.exit(
            f"{source} is {im.size[0]}x{im.size[1]}; need at least {MIN_SOURCE}px on the short side.\n"
            "  That is LinkedIn's download thumbnail, not your original upload -- ask for the\n"
            "  camera original, or pass --allow-small to accept a soft 2x avatar."
        )

    for path in (MASTER, AVATAR, OG_CARD, LI_PHOTO, LI_BANNER):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    # 1) master: keep the portrait, bounded so the repo does not carry 1MB photos.
    # Never replace a sharper master with a smaller source -- the LinkedIn
    # download is a 200px thumbnail and would throw the original away.
    existing = os.path.getsize(MASTER) if os.path.exists(MASTER) else 0
    existing_short = min(Image.open(MASTER).size) if existing else 0
    if existing_short > short:
        print(f"  master kept at {existing_short}px (source is {short}px; not downgrading)")
    else:
        master = im.copy()
        master.thumbnail((1200, 1200), RESAMPLE)
        master.save(MASTER, "JPEG", quality=86, optimize=True, progressive=True)

    # 2) avatar: 172px on the page, so 344 is exactly 2x
    sq = square(im, top)
    avatar = sq.resize((344, 344), RESAMPLE)
    avatar.save(AVATAR, "JPEG", quality=82, optimize=True, progressive=True)

    # 3) Open Graph card, 1200x630
    card = Image.new("RGB", (1200, 630), BASE)
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, 14, 630], fill=ACCENT)
    d.text((72, 150), "Dennis R. Gesker", font=font(BOLD, 74), fill=INK)
    d.text((72, 258), "Technology Executive", font=font(REG, 38), fill=ACCENT)
    d.text((72, 316), "CTO  ·  VP Engineering  ·  Director of Engineering", font=font(REG, 38), fill=SOFT)
    d.text((72, 470), "30+ years leading engineering, IT and product teams", font=font(REG, 38), fill=MUTED)
    d.text((72, 540), "dennis.gesker.com", font=font(REG, 32), fill=ACCENT)
    av = avatar.resize((300, 300), RESAMPLE)
    mask = Image.new("L", (300, 300), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 300, 300), fill=255)
    card.paste(av, (830, 165), mask)
    card.save(OG_CARD, "JPEG", quality=88, optimize=True, progressive=True)

    # 4) LinkedIn photo: same crop as the site avatar
    sq.resize((400, 400), RESAMPLE).save(LI_PHOTO, "JPEG", quality=88, optimize=True)

    # 5) LinkedIn banner 1584x396: text clear of the photo overlay and badge corner
    banner = Image.new("RGB", (1584, 396), BASE)
    d = ImageDraw.Draw(banner)
    d.rectangle([0, 0, 10, 396], fill=ACCENT)
    d.text((64, 88), "Dennis R. Gesker", font=font(BOLD, 60), fill=INK)
    d.text((64, 168), "Technology Executive", font=font(REG, 34), fill=ACCENT)
    d.text((64, 214), "CTO  ·  VP Engineering  ·  Director of Engineering", font=font(REG, 30), fill=SOFT)
    d.text((64, 300), "30+ years turning strategy into shipped systems", font=font(REG, 26), fill=MUTED)
    d.text((64, 338), "dennis.gesker.com", font=font(REG, 26), fill=ACCENT)
    d.text((1584 - 300, 110), "DG", font=font(BOLD, 150), fill=MONO)
    banner.save(LI_BANNER, "JPEG", quality=90, optimize=True, progressive=True)

    print(f"source: {source} {im.size[0]}x{im.size[1]}")
    if short < 344:
        print(f"  warning: avatar is upscaled {344 / short:.2f}x ({short}px -> 344px): it will read soft on a retina screen")
    for path in (MASTER, AVATAR, OG_CARD, LI_PHOTO, LI_BANNER):
        out = Image.open(path)
        print(f"  {path:<46} {out.size[0]}x{out.size[1]:<5} {os.path.getsize(path) // 1024:>4} KB")
    print("next: nix build, then `just publish` -- the avatar is baked into the PDFs' page one too")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
