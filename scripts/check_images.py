#!/usr/bin/env python3
"""Audit every image in src/images for visual consistency.

Reports, per image: pixel size, alpha coverage, the colour of the four corners
(is the background baked in?), the mean luminance of the opaque ink, and which
chip class the logo needs so it stays legible on the card background.

Chip classes used by theme/my.css:
    (none)                 transparent or dark ink -> surface chip
    info-logo--contrast    near-white ink -> dark chip, or it vanishes
    info-logo--white       white background baked in -> white chip, so the
                           square does not show as a lighter box on the card

Usage:
    python3 scripts/check_images.py [--dir src/images] [--json]
"""

import json
import os
import re
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow missing: pip install pillow")

WHITE_INK = 0.65  # mean luminance above this needs a dark chip
WHITE_BG = 0.96  # corner luminance above this means the white is baked in


def corners(im):
    w, h = im.size
    px = im.convert("RGBA")
    pts = []
    for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        pts.append(px.getpixel(xy))
    return pts


def classify(path):
    if path.lower().endswith(".svg"):
        # PIL cannot open vector files: read the declared fill colours instead
        text = open(path, encoding="utf-8", errors="replace").read()
        cols = sorted(set(re.findall(r'fill[:=]"?\s*(#[0-9a-fA-F]{3,8})', text)))
        lums = []
        for c in cols:
            c = c.lstrip("#")
            if len(c) == 3:
                c = "".join(ch * 2 for ch in c)
            if len(c) >= 6:
                r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
                lums.append((0.2126 * r + 0.7152 * g + 0.0722 * b) / 255)
        ink = min(lums) if lums else 0.0
        return {
            "file": os.path.basename(path),
            "px": "vector",
            "kb": round(os.path.getsize(path) / 1024, 1),
            "format": "SVG",
            "alpha": True,
            "coverage": 0.0,
            "bg": "transparent",
            "corner_lum": 0.0,
            "ink_lum": round(ink, 2),
            "chip": "info-logo--contrast" if ink > WHITE_INK else "",
            "square": False,
        }

    im = Image.open(path)
    fmt = im.format
    alpha_mode = im.mode in ("RGBA", "LA") or "transparency" in im.info
    rgba = im.convert("RGBA")
    w, h = rgba.size
    small = rgba.copy()
    small.thumbnail((96, 96), Image.LANCZOS)
    data = list(small.get_flattened_data() if hasattr(small, "get_flattened_data") else small.getdata())
    opaque = [(r, g, b) for r, g, b, a in data if a > 128]
    alpha_cov = len(opaque) / len(data) if data else 0
    ink = sum(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in opaque) / (255 * len(opaque)) if opaque else -1
    cs = corners(rgba)
    corner_lum = sum(0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b, a in cs if a > 128) / (
        255 * max(len([1 for *_, a in cs if a > 128]), 1)
    )
    corner_alpha = sum(a for *_, a in cs) / (4 * 255)

    if corner_alpha < 0.5:
        bg = "transparent"
    elif corner_lum > WHITE_BG:
        bg = "white"
    elif corner_lum < 0.2:
        bg = "dark"
    else:
        bg = "coloured"

    # The plate behind every logo is white in all flavours, so a baked-in white
    # background is seamless and a dark one keeps its own colour. Only a
    # near-white mark needs the dark plate.
    chip = "info-logo--contrast" if ink > WHITE_INK else ""
    return {
        "file": os.path.basename(path),
        "px": f"{w}x{h}",
        "kb": round(os.path.getsize(path) / 1024, 1),
        "format": fmt,
        "alpha": alpha_mode,
        "coverage": round(alpha_cov, 2),
        "bg": bg,
        "corner_lum": round(corner_lum, 2),
        "ink_lum": round(ink, 2),
        "chip": chip,
        "square": abs(w - h) <= 2,
    }


def main(argv):
    root = "src/images"
    if "--dir" in argv:
        root = argv[argv.index("--dir") + 1]
    files = sorted(
        os.path.join(root, f) for f in os.listdir(root) if f.lower().endswith((".png", ".jpg", ".jpeg", ".svg"))
    )
    # also the logos subdirectory
    logos = os.path.join(root, "logos")
    if os.path.isdir(logos):
        files += sorted(os.path.join(logos, f) for f in os.listdir(logos) if f.lower().endswith((".png", ".svg")))

    rows = [classify(f) for f in files]
    if "--json" in argv:
        print(json.dumps(rows, indent=1))
        return 0

    print(f"{'file':44} {'px':>10} {'kb':>6} {'bg':>12} {'ink':>5} {'chip needed'}")
    for r in rows:
        print(
            f"{r['file']:44} {r['px']:>10} {r['kb']:>6} {r['bg']:>12} "
            f"{r['ink_lum']:>5.2f} {r['chip']}"
        )

    counts = {}
    for r in rows:
        counts[r["bg"]] = counts.get(r["bg"], 0) + 1
    print()
    print("backgrounds:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    near_white = [r["file"] for r in rows if r["ink_lum"] > WHITE_INK]
    if near_white:
        print(f"{len(near_white)} near-white mark(s) -- need info-logo--contrast: {', '.join(near_white)}")
    mixed = len(counts) > 1
    print("MIXED backgrounds" if mixed else "uniform backgrounds")

    # Which chip classes the markdown actually applies
    md = []
    for base, _, names in os.walk("src"):
        # the *_short / resume_short variants are print-only fragments: print CSS
        # hides their floated logos, so they never render a chip
        if "resume_short" in base:
            continue
        for n in names:
            if n.endswith(".md") and not n.endswith("_short.md"):
                md.append(os.path.join(base, n))
    applied = {}
    for path in md:
        text = open(path, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'<img[^>]*src="(?:\.\./)?images/([^"]+)"[^>]*>', text):
            tag, src = m.group(0), m.group(1)
            cls = re.search(r'class="([^"]*)"', tag)
            applied[os.path.basename(src)] = cls.group(1) if cls else ""
    print()
    print("markdown usage:")
    problems = 0
    for r in rows:
        if r["file"] not in applied:
            continue
        have = applied[r["file"]]
        want = r["chip"]
        if want and want not in have:
            print(f"  {r['file']:42} has {have or '(no class)':24} needs {want}")
            problems += 1
        elif not want and "contrast" in have:
            print(f"  {r['file']:42} has contrast chip but ink is dark ({r['ink_lum']:.2f})")
            problems += 1
    if not problems:
        print("  every referenced image carries the right chip class")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
