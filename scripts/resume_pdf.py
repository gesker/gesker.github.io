#!/usr/bin/env python3
"""Build the résumé PDF that gets submitted, and prove it parses.

An ATS and an LLM screener both read this file, not the website. Three things
decide whether it scores:

  1. a real text layer, in reading order, one column, no glyph damage
  2. PDF metadata -- /Title, /Author, /Subject, /Keywords -- because most
     parsers read it and many keyword scorers index it
  3. section headings a parser recognises: SUMMARY, EXPERIENCE, EDUCATION,
     CERTIFICATIONS, PATENTS, PUBLICATIONS

This script prints the page, stamps the metadata, adds section bookmarks, then
extracts the text back out and checks the keywords are actually there. It fails
loudly rather than publishing a PDF a robot cannot read.

Usage:
    python3 scripts/resume_pdf.py ./book [--profile full|ats] [--out PATH]
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
CANONICAL = "https://dennis.gesker.com"

TITLE = "Dennis R. Gesker - Resume - Technology Executive (CTO / VP Engineering)"
AUTHOR = "Dennis R. Gesker"
SUBJECT = (
    "Resume of Dennis R. Gesker, technology executive: 30+ years leading engineering, "
    "IT and product teams. CTO, VP Engineering, Director of Engineering."
)
KEYWORDS = ", ".join(
    [
        "CTO",
        "VP Engineering",
        "Director of Engineering",
        "technology executive",
        "IT leadership",
        "enterprise architecture",
        "software engineering management",
        "platform engineering",
        "cloud architecture",
        "microservices",
        "Rust",
        "Java",
        "Jakarta EE",
        "Kubernetes",
        "Docker",
        "Podman",
        "NixOS",
        "Linux",
        "PostgreSQL",
        "DevOps",
        "CI/CD",
        "Terraform",
        "Ansible",
        "blockchain",
        "GIS",
        "SDLC",
        "Agile",
        "team leadership",
        "P&L",
        "cost reduction",
        "HIPAA",
        "TS/SCI",
    ]
)

# What a screener looks for. If any of these are missing from the text layer the
# PDF is broken, not merely imperfect.

# Two PDFs ship: the full résumé and a two-page version for portals that cap
# length or screen on the first two pages only.
PROFILES = {
    "full": {
        "page": "resume_full.html",
        "out": "Dennis_Gesker_Resume.pdf",
        "title": TITLE,
        "subject": SUBJECT,
        "required": [
            "Dennis R. Gesker",
            "Professional Experience",
            "Education",
            "Training and Certifications",
            "Patents Pending",
            "Publications",
            "Candela",
            "Montana State University",
            "Alamon",
            "Department of State",
            "Rust",
            "PostgreSQL",
        ],
        "bookmarks": [
            "Foundational Technologies",
            "Core Competencies",
            "Executive Profile",
            "Professional Experience",
            "Education",
            "Training and Certifications",
            "Patents Pending",
            "Publications",
            "Projects: High Impact",
            "Professional Organizations",
        ],
        "max_pages": 14,
    },
    "ats": {
        "page": "resume_ats.html",
        "out": "Dennis_Gesker_Resume_Short.pdf",
        "title": "Dennis R. Gesker - Resume Short - Technology Executive (ATS, two pages)",
        "subject": "Two-page ATS resume: technology executive, CTO / VP Engineering / Director of Engineering.",
        "required": [
            "Dennis R. Gesker",
            "Selected Highlights",
            "Professional Summary",
            "Core Competencies",
            "Professional Experience",
            "Education",
            "Certifications",
            "Patents",
            "Publications",
            "Candela",
            "Alamon",
            "Rust",
            "PostgreSQL",
        ],
        "bookmarks": [
            "Selected Highlights",
            "Professional Summary",
            "Core Competencies",
            "Professional Experience",
            "Education",
            "Certifications",
            "Patents",
            "Publications",
        ],
        "max_pages": 2,
    },
}

# Bookmark targets: heading text to look for on the page.


def print_pdf(page_path, out_path):
    profile = tempfile.mkdtemp(prefix="resume-pdf-chrome-")
    try:
        result = subprocess.run(
            [
                CHROME,
                "--headless=new",
                "--no-sandbox",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-gpu",
                f"--user-data-dir={profile}",
                "--no-pdf-header-footer",
                f"--print-to-pdf={out_path}",
                "file://" + os.path.abspath(page_path),
            ],
            capture_output=True,
            timeout=180,
        )
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 20000:
        sys.exit(f"printing failed: {result.stderr.decode('utf-8', 'replace')[-400:]}")


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    root = argv[1].rstrip("/")
    profile = argv[argv.index("--profile") + 1] if "--profile" in argv else "full"
    if profile not in PROFILES:
        sys.exit(f"unknown profile {profile!r}, expected one of {sorted(PROFILES)}")
    cfg = PROFILES[profile]
    out = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(root, cfg["out"])
    page = os.path.join(root, cfg["page"])
    if not os.path.exists(page):
        sys.exit(f"no {page} -- build first")

    try:
        import pymupdf
    except ImportError:
        sys.exit("pymupdf missing: pip install pymupdf (needed to stamp metadata and verify text)")

    print_pdf(page, out)

    doc = pymupdf.open(out)
    doc.set_metadata(
        {
            "title": cfg["title"],
            "author": AUTHOR,
            "subject": cfg["subject"],
            "keywords": KEYWORDS,
            "creator": "mdBook + scripts/resume_pdf.py",
            "producer": "Chromium print-to-pdf",
            "creationDate": pymupdf.get_pdf_now(),
            "modDate": pymupdf.get_pdf_now(),
        }
    )

    toc = []
    for i, page_obj in enumerate(doc, start=1):
        text = page_obj.get_text().lower()
        for name in cfg["bookmarks"]:
            if name.lower() in text and not any(t[1] == name for t in toc):
                toc.append([1, name, i])
    if toc:
        doc.set_toc(toc)
    # pymupdf refuses to rewrite the file it opened; save beside it and swap
    tmp_out = out + ".tmp"
    doc.save(tmp_out, garbage=4, deflate=True)
    doc.close()
    os.replace(tmp_out, out)

    # --- read it back the way a screener would -----------------------------
    doc = pymupdf.open(out)
    pages = [(p.get_text() or "") for p in doc]
    all_text = "\n".join(pages)
    words = len(all_text.split())
    problems = []

    missing = [k for k in cfg["required"] if k.lower() not in all_text.lower()]
    if missing:
        problems.append("text layer missing: " + ", ".join(missing))
    empty = [i + 1 for i, t in enumerate(pages) if len(t.strip()) < 200]
    if empty:
        problems.append(f"pages with almost no text (image-only?): {empty}")
    ligatures = [c for c in ("\ufb00", "\ufb01", "\ufb02", "\ufb03") if c in all_text]
    if ligatures:
        problems.append(f"ligature glyphs in text layer: {ligatures}")
    if words < (1500 if profile == "full" else 450):
        problems.append(f"only {words} words extracted")
    if len(pages) > cfg["max_pages"]:
        problems.append(f"{len(pages)} pages, {profile} profile allows {cfg['max_pages']}")
    # a masked phone number is a parsing failure for every ATS
    phone = re.search(r"\+?\d[\d\-\.\s]{7,}\d", all_text)
    phone_note = ""
    if not phone:
        phone_note = "no phone number in the text layer -- most ATS require one"
    elif "*" in phone.group(0):
        phone_note = f"phone is masked ({phone.group(0).strip()!r}) -- ATS phone parsers will fail; set a real number in src/address.md"

    meta = doc.metadata or {}
    print(f"file:      {out} ({os.path.getsize(out) / 1024:.0f} KB)")
    print(f"pages:     {len(pages)}")
    print(f"words:     {words}")
    print(f"bookmarks: {len(toc)}")
    print(f"title:     {meta.get('title', '')[:70]}")
    print(f"author:    {meta.get('author', '')}")
    print(f"keywords:  {len(meta.get('keywords', '').split(','))} terms")
    if phone_note:
        print(f"warning:   {phone_note}")
    print()
    if problems:
        print(f"{len(problems)} problem(s):")
        for line in problems:
            print("  " + line)
        return 1
    print("text layer and metadata verified: this PDF parses")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
