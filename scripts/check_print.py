#!/usr/bin/env python3
"""Check a printed mdBook PDF for broken page breaks.

Looks at where things actually land on the page, not just the page count:

  orphan heading  a heading is the last thing on a page
  leading heading a page starts with a heading (fine, but worth seeing)
  thin tail       a page ends with a single short line of a paragraph
  sparse page     a page holds far less text than the average
  fill            how much of the printable column the page actually uses

Usage:
    python3 scripts/check_print.py resume.pdf [--min-fill 0.45] [--json]

Exit code is 1 if any orphan heading, thin tail or sparse page is found, so it
can gate a publish.
"""

import json
import sys

try:
    import pymupdf
except ImportError:  # pragma: no cover
    sys.exit("pymupdf missing: pip install pymupdf")


HEADING_MIN_SIZE = 12.5


def analyse(path, min_fill=0.45):
    doc = pymupdf.open(path)
    pages = []
    for pno, page in enumerate(doc, start=1):
        blocks = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                blocks.append(
                    {
                        # spans in a line are contiguous: joining with a space
                        # invents gaps and made clean text look garbled
                        "text": "".join(s["text"] for s in spans).strip(),
                        "size": max(s["size"] for s in spans),
                        "bold": any("Bold" in s["font"] or s["flags"] & 16 for s in spans),
                        "top": line["bbox"][1],
                        "bottom": line["bbox"][3],
                    }
                )
        blocks.sort(key=lambda b: b["top"])
        height = page.rect.height
        top_margin = min((b["top"] for b in blocks), default=0)
        bottom = max((b["bottom"] for b in blocks), default=0)
        usable = height - 2 * top_margin if top_margin else height
        fill = (bottom - top_margin) / usable if usable else 0
        chars = sum(len(b["text"]) for b in blocks)
        pages.append(
            {
                "page": pno,
                "blocks": blocks,
                "chars": chars,
                "fill": round(min(fill, 1.0), 3),
                "first": blocks[0]["text"][:60] if blocks else "",
                "last": blocks[-1] if blocks else None,
                "starts_with_heading": bool(blocks) and blocks[0]["size"] >= HEADING_MIN_SIZE,
            }
        )

    avg_chars = sum(p["chars"] for p in pages) / len(pages) if pages else 0
    for p in pages:
        last = p["last"]
        # A heading alone at the foot of the page: big or bold text, short, and
        # it is the final thing on the page.
        p["orphan_heading"] = bool(
            last
            and (last["size"] >= HEADING_MIN_SIZE or last["bold"])
            and len(last["text"]) < 90
            and last["top"] > p["blocks"][0]["top"] + 40
        )
        # A single short line at the foot is only a problem when the page had
        # room to hold more: at 0.9 fill the short line is just the last line
        # of a paragraph, which is normal typesetting.
        p["thin_tail"] = bool(
            last
            and not p["orphan_heading"]
            and len(last["text"]) < 55
            and p["page"] != len(pages)
            and p["fill"] < 0.80
        )
        # the last page is the end of the document and is always partial
        p["sparse"] = bool(p["fill"] < 0.7 and p["page"] != len(pages))
        # the last page is the end of the document: partial by definition
        p["low_fill"] = p["fill"] < min_fill and p["page"] != len(pages)
    return pages


def main(argv):
    if len(argv) < 2:
        sys.exit("usage: check_print.py <pdf> [--min-fill 0.45] [--json]")
    path = argv[1]
    min_fill = 0.45
    if "--min-fill" in argv:
        min_fill = float(argv[argv.index("--min-fill") + 1])
    pages = analyse(path, min_fill)

    # Hard failures break the document; warnings are cosmetic (a paragraph's
    # last line is short, a bullet that will not split leaves a gap).
    problems, warnings = [], []
    for p in pages:
        if p["orphan_heading"]:
            problems.append(f"page {p['page']}: orphan heading -> {p['last']['text'][:50]!r}")
        if p["sparse"]:
            problems.append(f"page {p['page']}: sparse, {p['chars']} chars vs avg, fill {p['fill']:.2f}")
        if p["thin_tail"]:
            warnings.append(f"page {p['page']}: short final line, fill {p['fill']:.2f} -> {p['last']['text'][:40]!r}")
        if p["low_fill"]:
            warnings.append(f"page {p['page']}: low fill {p['fill']:.2f}")

    if "--json" in argv:
        print(json.dumps({"pages": pages, "problems": problems}, indent=1))
    else:
        print(f"{'pg':>3} {'chars':>6} {'fill':>5}  {'ends with':<52} problems")
        for p in pages:
            last = (p["last"]["text"] if p["last"] else "")[:50]
            flags = []
            if p["orphan_heading"]:
                flags.append("ORPHAN-HEADING")
            if p["thin_tail"]:
                flags.append("thin-tail")
            if p["sparse"]:
                flags.append("sparse")
            if p["low_fill"]:
                flags.append("low-fill")
            print(f"{p['page']:>3} {p['chars']:>6} {p['fill']:>5.2f}  {last:<52} {','.join(flags)}")
        print()
        print(f"pages: {len(pages)}  avg chars: {sum(p['chars'] for p in pages) // max(len(pages), 1)}")
        if warnings:
            print(f"{len(warnings)} cosmetic warning(s):")
            for line in warnings:
                print("  " + line)
        if problems:
            print(f"{len(problems)} problem(s):")
            for line in problems:
                print("  " + line)
        elif not warnings:
            print("no break problems found")
    return 1 if any(p["orphan_heading"] or p["sparse"] for p in pages) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
