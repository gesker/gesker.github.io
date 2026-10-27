#!/usr/bin/env python3
"""Add the search and social metadata mdBook does not generate.

Every page mdBook builds gets one identical <meta name="description"> and no
canonical, no Open Graph, no structured data, no sitemap and no robots.txt. For
a personal site that is the difference between being found and not.

This script post-processes the built book and writes:

  * a canonical link on the real domain (dennis.gesker.com), independent of
    site-url, which has to stay on the github.io host for Pages to publish
  * a per-page description, hand-written rather than scraped
  * Open Graph + Twitter card tags, so a link pasted into LinkedIn or a DM
    renders a preview instead of a bare URL
  * schema.org Person JSON-LD, which is what makes a search engine understand
    this is one person with a job history, not a blog
  * robots.txt and sitemap.xml
  * noindex on the 404 page, the print page and the pdf-only artifacts

Usage:
    python3 scripts/seo.py ./book
    python3 scripts/seo.py ./book --check
"""

import html as htmlmod
import json
import os
import re
import sys
import time

CANONICAL = "https://dennis.gesker.com"
SITE_NAME = "Dennis R. Gesker"
OG_IMAGE = "/images/og-card.jpg"

DESCRIPTIONS = {
    "index.html": "Dennis R. Gesker — technology executive with 30+ years leading engineering, IT and product teams. Architecture, delivery, and the people who do the work.",
    "about.html": "Dennis R. Gesker — CTO, VP Engineering and Director of IT with 30+ years across defense, government, energy and software products.",
    "resume_full.html": "The complete résumé of Dennis R. Gesker: 30+ years of technology leadership across Candela Global, Montana State University, Alamon and the U.S. Department of State.",
    "professional.html": "Professional history of Dennis R. Gesker — CTO and VP Engineering roles at Candela Global, Montana State University, Alamon, Inc. and the U.S. Department of State.",
    "portfolio.html": "Selected work by Dennis R. Gesker: Candela Global, pending patents in blockchain monitoring and price discovery, registered trademarks and published writing.",
    "publications.html": "Published writing by Dennis R. Gesker — Linux Journal, InfoQ, SysAdmin Magazine, BYTE and U.S. Department of State strategy papers.",
    "patents_pending.html": "Pending U.S. patent applications by Dennis R. Gesker: distributed blockchain monitoring with latency compensation, and economic price discovery in social networks.",
    "trademarks.html": "Registered trademark held by Dennis R. Gesker — the Zalag mark, Quaerite Lux et Sapientia.",
    "organizations.html": "Professional organizations Dennis R. Gesker belongs to: Jakarta EE Ambassadors leadership council, Eclipse Foundation, IEEE, ACM-adjacent JCP, EFF and the Society of Catholic Scientists.",
    "awards.html": "Awards and recognition for Dennis R. Gesker — Alamon President's Award for Innovation and U.S. Department of State Extra Mile and Certificate of Appreciation.",
    "education.html": "Education: University of Pittsburgh, Katz Graduate School of Business, Drexel University and Central High School.",
    "certifications.html": "Training and certifications for Dennis R. Gesker — FCC licenses, Duke/Coursera specializations, TechStrong and the Foreign Service Institute.",
    "projects.html": "High-impact projects delivered by Dennis R. Gesker — Tabulare, Aveum Systems, AlaTrac, and the infrastructure and reporting programs behind them.",
    "background.html": "Background and summary for Dennis R. Gesker — 30 years spanning engineering, IT leadership and product delivery.",
    "profile.html": "Executive profile of Dennis R. Gesker: what he owns, how he leads, and the results behind the résumé.",
    "foundational_technologies.html": "The technologies Dennis R. Gesker builds on — Linux, Rust, Java and Jakarta EE, PostgreSQL, Nix, containers, cloud and enterprise integration.",
    "resume_ats.html": "Résumé Short: the two-page résumé of Dennis R. Gesker, technology executive: selected highlights, experience, education, certifications, patents and publications.",
    "404.html": "Page not found.",
}

# The home page and the Welcome chapter both render <title>Welcome</title>.
# Duplicate titles across two indexable pages compete with each other.
TITLES = {
    "index.html": "Dennis R. Gesker — Technology Executive, CTO / VP Engineering",
    "about.html": "Welcome — Dennis R. Gesker",
    "resume_full.html": "Résumé Full — Dennis R. Gesker",
    "resume_ats.html": "Résumé Short (two pages) — Dennis R. Gesker",
    "404.html": "Page not found — Dennis R. Gesker",
}

PERSON = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "Dennis R. Gesker",
    "givenName": "Dennis",
    "additionalName": "R.",
    "familyName": "Gesker",
    "jobTitle": "Chief Technology Officer",
    "email": "mailto:dennis@gesker.com",
    "telephone": "+1-202-798-3202",
    "url": CANONICAL + "/",
    "image": CANONICAL + OG_IMAGE,
    "description": (
        "Technology executive with 30+ years leading engineering, IT and product teams across "
        "software products, government service, energy and field operations."
    ),
    "address": {
        "@type": "PostalAddress",
        "addressLocality": "Bozeman",
        "addressRegion": "MT",
        "addressCountry": "US",
    },
    "worksFor": {"@type": "Organization", "name": "Candela Global, LLC", "url": "https://candela.global"},
    "alumniOf": [
        {"@type": "CollegeOrUniversity", "name": "University of Pittsburgh"},
        {"@type": "CollegeOrUniversity", "name": "Drexel University"},
    ],
    "sameAs": [
        "https://www.linkedin.com/in/gesker",
        "https://github.com/gesker",
        "https://gesker.wordpress.com",
        "https://www.linuxjournal.com/users/dennis-gesker",
        "https://www.infoq.com/profile/Dennis-Gesker/",
    ],
    "knowsAbout": [
        "IT Strategy",
        "Enterprise Architecture",
        "Software Development Life Cycle",
        "Agile Software Development",
        "Team Leadership",
        "Technical Staff Development",
        "Project Management",
        "Linux",
        "Rust",
        "Java",
        "Jakarta EE",
        "PostgreSQL",
        "Nix",
        "Container Orchestration",
        "Cloud Architecture",
        "Microservices",
        "Blockchain",
        "Geographic Information Systems",
    ],
    "seeks": {
        "@type": "Demand",
        "name": "Executive technology leadership role — CTO, VP Engineering or Director of Engineering",
    },
}

INDEXABLE_EXCEPT = {"404.html", "print.html", "toc.html"}
NOINDEX_SUFFIX = ("_for_pdf_only.html",)
NOINDEX_PREFIX = ("resume_short/",)


def page_url(name):
    if name in ("index.html", "404.html"):
        return CANONICAL + "/"
    return f"{CANONICAL}/{name}"


def esc(text):
    return htmlmod.escape(text, quote=True)


def build_block(name, description):
    url = page_url(name)
    og_type = "profile" if name in ("index.html", "about.html", "resume_full.html") else "article"
    title = SITE_NAME if name == "index.html" else None
    lines = [
        f'<link rel="canonical" href="{url}">',
        f'<meta name="description" content="{esc(description)}">',
        '<meta property="og:locale" content="en_US">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="{esc(SITE_NAME)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:description" content="{esc(description)}">',
        f'<meta property="og:image" content="{CANONICAL}{OG_IMAGE}">',
        '<meta property="og:image:type" content="image/jpeg">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="Dennis R. Gesker, Technology Executive">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:description" content="{esc(description)}">',
        f'<meta name="twitter:image" content="{CANONICAL}{OG_IMAGE}">',
    ]
    if title:
        lines.insert(4, f'<meta property="og:title" content="{esc(title)}">')
        lines.insert(5, f'<meta name="twitter:title" content="{esc(title)}">')
    graph = [PERSON]
    if name in ("index.html", "about.html", "resume_full.html"):
        graph.append(
            {
                "@context": "https://schema.org",
                "@type": "ProfilePage",
                "url": url,
                "name": f"{SITE_NAME} — résumé" if name == "resume_full.html" else SITE_NAME,
                "about": {"@type": "Person", "name": SITE_NAME},
                "mainEntity": {"@type": "Person", "name": SITE_NAME, "url": CANONICAL + "/"},
            }
        )
    lines.append('<script type="application/ld+json">' + json.dumps(graph[0] if len(graph) == 1 else {"@context": "https://schema.org", "@graph": graph}) + "</script>")
    return "\n        ".join(lines)


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    root = argv[1].rstrip("/")
    check = "--check" in argv
    # toc.html is mdbook's sidebar helper, not a page
    pages = [n for n in sorted(os.listdir(root)) if n.endswith(".html") and n != "toc.html"]
    if not pages:
        sys.exit(f"no html pages in {root} -- build first")

    changed, problems = 0, []
    for name in pages:
        path = os.path.join(root, name)
        page = open(path, encoding="utf-8", errors="replace").read()
        description = DESCRIPTIONS.get(name) or DESCRIPTIONS["about.html"]
        noindex = (
            'http-equiv="refresh"' in page  # a redirect stub for a retired URL
            or name in INDEXABLE_EXCEPT
            or name.endswith(NOINDEX_SUFFIX)
            or name.startswith(NOINDEX_PREFIX)
            or name.startswith("resume_short")
        )

        # drop what mdbook wrote, add ours
        body = re.sub(r'\s*<meta name="description"[^>]*>', "", page)
        body = re.sub(r'\s*<link rel="canonical"[^>]*>', "", body)
        body = re.sub(r"\s*<meta (?:property|name)=\"(?:og|twitter)[^\"]*\"[^>]*>", "", body)
        body = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', "", body, flags=re.S)
        body = re.sub(r'\s*<meta name="robots"[^>]*>', "", body)

        if name in TITLES:
            body = re.sub(r"<title>.*?</title>", f"<title>{esc(TITLES[name])}</title>", body, count=1, flags=re.S)
        block = build_block(name, description)
        if noindex:
            block = '<meta name="robots" content="noindex, follow">\n        ' + block
        if "</title>" not in body:
            problems.append(f"{name}: no </title> (not a real page?)")
            continue
        new = body.replace("</title>", "</title>\n        " + block, 1)
        if check:
            # compare markers, not whole files: the download links are injected
            # later and make a byte comparison fail for no good reason
            needed = [
                f'<link rel="canonical" href="{page_url(name)}">',
                'application/ld+json',
                'property="og:image"',
                f'content="{esc(description)}"',
            ]
            if noindex:
                needed.append('name="robots" content="noindex')
            missing = [n for n in needed if n not in page]
            if missing:
                problems.append(f"{name}: metadata missing ({missing[0][:60]})")
            continue
        if new == page:
            continue
        open(path, "w").write(new)
        changed += 1

    # robots.txt + sitemap.xml
    today = time.strftime("%Y-%m-%d")
    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /print.html\n"
        "Disallow: /resume_short/\n"
        f"Sitemap: {CANONICAL}/sitemap.xml\n"
    )
    def is_stub(n):
        html = open(os.path.join(root, n), encoding="utf-8", errors="replace").read()
        return 'http-equiv="refresh"' in html

    indexable = [
        n
        for n in pages
        if n not in INDEXABLE_EXCEPT
        and not n.endswith(NOINDEX_SUFFIX)
        and not n.startswith("resume_short")
        and not is_stub(n)
    ]
    urls = []
    for n in indexable:
        loc = CANONICAL + "/" if n == "index.html" else f"{CANONICAL}/{n}"
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod></url>")
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    )
    for fname, content in (("robots.txt", robots), ("sitemap.xml", sitemap)):
        path = os.path.join(root, fname)
        existing = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if existing == content:
            continue
        if check:
            problems.append(f"{fname}: missing or stale")
            continue
        open(path, "w").write(content)
        changed += 1

    # link the machine-readable exports from the resume pages themselves
    for resume_name, links in (
        ("resume_full.html", "PDF"),
        ("resume_ats.html", "PDF"),
    ):
      resume_page = os.path.join(root, resume_name)
      if not os.path.exists(os.path.join(root, "Dennis_Gesker_Resume.pdf")) or not os.path.exists(resume_page):
        continue
      if True:
        page = open(resume_page, encoding="utf-8", errors="replace").read()
        if 'href="/Dennis_Gesker_Resume.pdf"' not in page:
            extra = (
                '<span class="resume-downloads no-print" style="margin-left:auto;font-size:13px">'
                '<a href="/Dennis_Gesker_Resume.pdf">Résumé Full (PDF)</a> &middot; '
                '<a href="/Dennis_Gesker_Resume_Short.pdf">Résumé Short (PDF)</a> &middot; '
                '<a href="/resume.txt">Plain text (ATS)</a> &middot; '
                '<a href="/resume.json">JSON</a></span>'
            )
            new = page.replace("</p>", extra + "</p>", 1) if 'class="resume-toolbar' in page else page
            if new != page:
                if not check:
                    open(resume_page, "w", encoding="utf-8").write(new)
                    changed += 1
                else:
                    problems.append("resume_full.html: download links missing")
            # machines find it even without the link
            if '<link rel="alternate" type="text/plain"' not in page and not check:
                open(resume_page, "w", encoding="utf-8").write(
                    new.replace(
                        "</title>",
                        '</title>\n        <link rel="alternate" type="text/plain" href="/resume.txt">',
                        1,
                    )
                )

    # llms.txt: the emerging convention for telling an LLM agent what a site is
    # and where the machine-readable version lives
    llms = [
        f"# {SITE_NAME}",
        "",
        "> Technology executive with 30+ years leading engineering, IT and product teams.",
        "",
        "## Machine-readable",
        f"- [Resume Full, plain text]({CANONICAL}/resume.txt): full resume, ATS-shaped, one column, no tables",
        f"- [Resume Full, PDF]({CANONICAL}/Dennis_Gesker_Resume.pdf): full resume, metadata, section bookmarks",
        f"- [Resume Short, two-page PDF]({CANONICAL}/Dennis_Gesker_Resume_Short.pdf): curated two-page version for portals that cap length",
        f"- [Resume Full, JSON]({CANONICAL}/resume.json): basics plus sections split by heading",
        "",
        "## Profiles",
        "- [LinkedIn](https://www.linkedin.com/in/gesker/)",
        "- [GitHub](https://github.com/gesker)",
        "- [Blog](https://gesker.wordpress.com)",
        "",
        "## Pages",
    ]
    for n in indexable:
        if n.endswith((".txt", ".json", ".pdf")):
            continue
        label = n[:-5].replace("_", " ")
        llms.append(f"- [{label}]({CANONICAL}/{n}): {DESCRIPTIONS.get(n, '')}")
    llms_txt = "\n".join(llms) + "\n"
    llms_path = os.path.join(root, "llms.txt")
    existing = open(llms_path, encoding="utf-8").read() if os.path.exists(llms_path) else ""
    if existing != llms_txt:
        if check:
            problems.append("llms.txt: missing or stale")
        else:
            open(llms_path, "w", encoding="utf-8").write(llms_txt)
            changed += 1

    if problems:
        print(f"{len(problems)} SEO problem(s):")
        for line in problems:
            print("  " + line)
        return 1
    print(f"{len(indexable)} indexable pages, {len(pages)} total; {changed} file(s) written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
