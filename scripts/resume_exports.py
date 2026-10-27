#!/usr/bin/env python3
"""Publish the résumé in the shapes machines want to read.

An ATS parses a file, not a web page, and an LLM summarising a candidate would
rather read text than scrape HTML. Both are generated from the built résumé page
so there is still one source of truth: src/resume_full.md and its includes.

Writes, next to the built pages:

    resume.txt   plain text, ATS-shaped header, standard section order, no
                 tables, no columns, no glyphs a parser chokes on
    resume.json  basics plus each section split at its heading, for anything
                 that would rather have structure than prose

Usage:
    python3 scripts/resume_exports.py ./book
"""

import html as htmlmod
import json
import os
import re
import sys

CANONICAL = "https://dennis.gesker.com"

# Section headings in the résumé, mapped to the names an ATS expects. Anything
# not listed keeps its own text, upper-cased.
ATS_HEADINGS = {
    "Foundational Technologies": "TECHNICAL SKILLS",
    "Core Competencies": "CORE COMPETENCIES",
    "Selected Highlights": "SELECTED HIGHLIGHTS",
    "Executive Profile": "PROFESSIONAL SUMMARY",
    "Background / Summary": "BACKGROUND",
    "Professional Organizations": "PROFESSIONAL ORGANIZATIONS",
    "Training and Certifications": "CERTIFICATIONS AND TRAINING",
    "Patents Pending": "PATENTS",
    "Publications": "PUBLICATIONS",
    "Education": "EDUCATION",
    "Projects: High Impact": "PROJECTS",
    "Trademarks": "TRADEMARKS",
    "Awards": "AWARDS",
}

# The employer cards carry no heading in the source, so the experience section
# has no boundary of its own. These are the first lines of each card.
EXPERIENCE_MARKERS = (
    "Candela Global",
    "Montana State University",
    "Alamon, Inc.",
    "United States Department of State",
)

# ATS wants the summary first and the history before the appendices.
SECTION_ORDER = [
    "SELECTED HIGHLIGHTS",
    "PROFESSIONAL SUMMARY",
    "BACKGROUND",
    "CORE COMPETENCIES",
    "TECHNICAL SKILLS",
    "PROFESSIONAL EXPERIENCE",
    "EDUCATION",
    "CERTIFICATIONS AND TRAINING",
    "PATENTS",
    "PUBLICATIONS",
    "PROJECTS",
    "AWARDS",
    "TRADEMARKS",
    "PROFESSIONAL ORGANIZATIONS",
]

BLOCK_TAGS = "p|div|li|section|article|ul|ol|blockquote"


def to_text(page):
    """Turn the résumé page into plain text, headings and table rows preserved."""
    body = page.split("<main>", 1)[-1].split("</main>", 1)[0]
    body = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", body, flags=re.S | re.I)
    # the print button is chrome, not résumé content
    body = re.sub(r'<[^>]*(?:resume-toolbar|no-print)[^>]*>.*?</\w+>', " ", body, flags=re.S | re.I)
    # navigation chrome: related lines, section chips, page badges, footer
    body = re.sub(
        r'<[^>]*class="[^"]*(?:related|page-badge|toc-chips|hero-jumps|site-footer)[^"]*"[^>]*>.*?</\w+>',
        " ",
        body,
        flags=re.S | re.I,
    )
    body = re.sub(r"<img\b[^>]*>", " ", body, flags=re.I)
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)

    def heading(m):
        inner = m.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        if not text:
            return "\n"
        return f"\n\n{ATS_HEADINGS.get(text, text.upper())}\n"

    body = re.sub(r"<h([1-4])[^>]*>(.*?)</h\1>", heading, body, flags=re.S | re.I)
    # table cells stay distinguishable instead of running together
    body = re.sub(r"</t[dh]>", " | ", body, flags=re.I)
    body = re.sub(r"</tr>", "\n", body, flags=re.I)
    body = re.sub(rf"</?(?:{BLOCK_TAGS})\b[^>]*>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", "", body)
    body = htmlmod.unescape(body)

    for bad, good in (
        ("\u2014", " - "),
        ("\u2013", "-"),
        ("\u1427", "\u00b7"),  # stray syllabics glyph, if any source still has one
        ("\u2019", "'"),
        ("\u2018", "'"),
        ("\u201c", '"'),
        ("\u201d", '"'),
        ("\u00a0", " "),
    ):
        body = body.replace(bad, good)

    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r" *\| *\|+ *", " | ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    lines = [line.strip() for line in body.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def split_sections(text):
    """Split at headings, mark the experience block, drop duplicate headings."""
    names = set(ATS_HEADINGS.values())
    out, current, buf = [], "HEADER", []
    for line in text.split("\n"):
        # A card heading is upper-cased, short, and starts with the employer
        # name. Matching on the text alone caught "Alamon" inside prose.
        started_experience = (
            current not in ("PROFESSIONAL EXPERIENCE",)
            and len(line) < 110
            and line == line.upper()
            and any(line.startswith(m.upper()) for m in EXPERIENCE_MARKERS)
        )
        if started_experience:
            # the page has a real "Professional Experience" heading just above
            # the first card; do not emit it twice
            while buf and buf[-1].strip() == "PROFESSIONAL EXPERIENCE":
                buf.pop()
            if buf:
                out.append((current, buf))
            current, buf = "PROFESSIONAL EXPERIENCE", [line]
            continue
        if line in names:
            if buf:
                out.append((current, buf))
            current, buf = line, []
        else:
            buf.append(line)
    if buf:
        out.append((current, buf))

    # collapse repeats (technical skills and core competencies both appear twice)
    merged = {}
    for name, lines in out:
        merged.setdefault(name, []).extend(lines)
    ordered = [k for k in SECTION_ORDER if k in merged]
    ordered += [k for k in merged if k not in ordered]
    return [(k, merged[k]) for k in ordered]


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    root = argv[1].rstrip("/")
    src = os.path.join(root, "resume_full.html")
    if not os.path.exists(src):
        sys.exit(f"no {src} -- build first")
    page = open(src, encoding="utf-8", errors="replace").read()

    text = to_text(page)
    if len(text) < 2000:
        sys.exit(f"extracted only {len(text)} chars from the resume -- refusing to publish that")

    sections = split_sections(text)
    named = {name: lines for name, lines in sections}

    header = [
        "DENNIS R. GESKER",
        "Technology Executive - CTO / VP Engineering / Director of Engineering",
        "Bozeman, Montana, United States",
        "dennis@gesker.com",
        "+1 202-798-3202",
        "https://dennis.gesker.com",
        "",
        f"Résumé: {CANONICAL}/resume_full.html",
        f"Plain text: {CANONICAL}/resume.txt | JSON: {CANONICAL}/resume.json",
    ]
    parts = ["\n".join(header)]
    for name, lines in sections:
        if name == "HEADER":
            # already replaced by the header above
            continue
        parts.append(f"{name}\n" + "\n".join(lines))
    resume_txt = "\n\n".join(parts).strip() + "\n"
    open(os.path.join(root, "resume.txt"), "w", encoding="utf-8").write(resume_txt)

    doc = {
        "$comment": (
            "Generated from https://dennis.gesker.com/resume_full.html by "
            "scripts/resume_exports.py -- do not edit by hand"
        ),
        "basics": {
            "name": "Dennis R. Gesker",
            "label": "Technology Executive - CTO / VP Engineering",
            "email": "dennis@gesker.com",
            "url": f"{CANONICAL}/resume_full.html",
            "summary": named.get("PROFESSIONAL SUMMARY", []),
            "location": {"city": "Bozeman", "region": "MT", "countryCode": "US"},
            "profiles": [
                {"network": "LinkedIn", "url": "https://www.linkedin.com/in/gesker"},
                {"network": "GitHub", "url": "https://github.com/gesker"},
                {"network": "Blog", "url": "https://gesker.wordpress.com"},
            ],
        },
        "sections": [
            {"name": name, "lines": lines} for name, lines in sections if name != "HEADER"
        ],
    }
    open(os.path.join(root, "resume.json"), "w", encoding="utf-8").write(
        json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    )

    print(f"resume.txt: {len(resume_txt)} chars, {len(resume_txt.split())} words")
    print(f"resume.json: {len(doc['sections'])} sections")
    for name, lines in sections:
        print(f"  {name:<32} {len(lines):>3} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
