#!/usr/bin/env python3
"""Check the font progression across every built page.

A site reads as one site when the same level is the same size everywhere and the
sizes descend in a predictable order:

    display > h1 > h2 > h3 > h4 > body >= small print > micro label

For every page this measures the computed font-size of each level and reports:

  * the size used per level, per page
  * a level that is larger than the level above it
  * a level whose size differs from the site-wide size for that level
  * a step between adjacent levels too small to read as hierarchy, or so large
    that the scale looks accidental

Pages load over file:// from an injected copy of the built site: driving them
over HTTP dropped stylesheets at random, so measurements came back unstyled.

Usage:
    python3 scripts/check_type.py [--dir result] [--json] [pages...]
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

# Ordered from largest to smallest by role. `display` is the hero name, which is
# deliberately larger than a page title.
LEVELS = [
    ("display", ".hero-name"),
    ("h1", "h1:not(.hero-name)"),
    ("h2", "h2"),
    ("h3", "h3"),
    ("h4", "h4"),
    (
        "body",
        "p:not(.related):not(.page-badge):not(.contact-line):not(.resume-toolbar)"
        ":not([class^='hero-'])",
    ),
    ("list", "li"),
    ("cardTitle", ".info-card > h3, .info-title"),
    ("cardSub", ".info-sub"),
    ("cardMeta", ".info-meta"),
    ("related", "p.related"),
    ("chip", ".toc-chips a"),
    ("footer", ".site-footer"),
    ("eyebrow", ".hero-eyebrow"),
]

# Only this run must descend monotonically: body and list are one size by
# design, and the small-print group is deliberately close together.
HIERARCHY = ["display", "h1", "h2", "h3", "h4", "body"]

PROBE = r"""
<script>
window.addEventListener('load', function () {
  const main = document.querySelector('.content main') || document.body;
  // Scope strictly to the page body. A document-wide fallback picked up the
  // sidebar's 14px list items and the nav's headings and reported them as
  // page content.
  const q = s => main.querySelector(s);
  const outside = s => document.querySelector(s);
  // Card headings are a component with their own size; a section heading is one
  // that is not inside a card. Measure them separately or the two collide.
  const section = s => {
    for (const el of main.querySelectorAll(s)) {
      if (!el.closest('.info-card') && !el.closest('.info-grid')) return el;
    }
    return null;
  };
  const out = { page: location.pathname, sheets: document.styleSheets.length, sizes: {}, weights: {} };
  out.cssOk = getComputedStyle(document.documentElement).getPropertyValue('--space-4').trim() !== '';
  const OUTSIDE = { footer: 1 };
  %LEVELS%.forEach(function (pair) {
    const el = OUTSIDE[pair[0]] ? outside(pair[1])
      : (pair[0].startsWith('h') ? section(pair[1]) : q(pair[1]));
    if (!el) { out.sizes[pair[0]] = null; return; }
    const cs = getComputedStyle(el);
    out.sizes[pair[0]] = Math.round(parseFloat(cs.fontSize) * 100) / 100;
    out.weights[pair[0]] = cs.fontWeight;
  });
  const d = document.createElement('div');
  d.id = 'typescale';
  d.textContent = 'TYPE::' + JSON.stringify(out);
  document.body.appendChild(d);
});
</script>
"""


def prepare(root):
    """Copy the built site somewhere writable and inject the probe into every page."""
    tmp = tempfile.mkdtemp(prefix="type-site-")
    site = os.path.join(tmp, "site")
    shutil.copytree(os.path.realpath(root), site)
    # the nix store is read-only and copytree keeps the mode
    for base, _, names in os.walk(site):
        for n in names:
            os.chmod(os.path.join(base, n), 0o644)
    probe = PROBE.replace("%LEVELS%", json.dumps(LEVELS))
    for name in os.listdir(site):
        if not name.endswith(".html"):
            continue
        path = os.path.join(site, name)
        body = open(path, encoding="utf-8", errors="replace").read()
        body = re.sub(r'<base href="[^"]*">', "", body)
        if "</body>" in body:
            open(path, "w").write(body.replace("</body>", probe + "</body>"))
    return tmp, site


def measure(site, page, attempts=3):
    profile = tempfile.mkdtemp(prefix="type-chrome-")
    try:
        html = subprocess.run(
            [
                CHROME,
                "--headless=new",
                "--no-sandbox",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-gpu",
                f"--user-data-dir={profile}",
                "--disk-cache-size=1",
                "--window-size=1440,1200",
                "--virtual-time-budget=15000",
                "--blink-settings=preferredColorScheme=1",
                "--dump-dom",
                "file://" + os.path.join(site, page),
            ],
            capture_output=True,
            timeout=150,
        ).stdout.decode("utf-8", "replace")
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    m = re.search(r'<div id="typescale">TYPE::(.*?)</div>', html, re.S)
    if not m:
        return None
    import html as htmlmod

    data = json.loads(htmlmod.unescape(m.group(1)))
    if not data.get("cssOk", True) and attempts > 1:
        return measure(site, page, attempts - 1)
    return data


def main(argv):
    root = "result"
    if "--dir" in argv:
        root = argv[argv.index("--dir") + 1]
    requested = [a for a in argv[1:] if not a.startswith("--") and a != root and a.endswith(".html")]
    pages = requested or [
        n
        for n in sorted(os.listdir(root))
        if n.endswith(".html") and n not in ("print.html", "toc.html") and not n.endswith("_for_pdf_only.html")
    ]

    tmp, site = prepare(root)
    rows = []
    try:
        for page in pages:
            r = measure(site, page)
            rows.append(r if r else {"page": "/" + page, "sizes": {}, "weights": {}, "failed": True})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if "--json" in argv:
        print(json.dumps(rows, indent=1))
        return 0

    names = [n for n, _ in LEVELS]
    print(f"{'page':28} " + " ".join(f"{n:>8}" for n in names))
    for r in rows:
        cells = []
        for n in names:
            v = r["sizes"].get(n)
            cells.append(f"{v:>8.1f}" if isinstance(v, (int, float)) else f"{'-':>8}")
        print(f"{r['page'][:28]:28} " + " ".join(cells))

    ref = {}
    for n in names:
        vals = [r["sizes"].get(n) for r in rows if isinstance(r["sizes"].get(n), (int, float))]
        if vals:
            ref[n] = max(set(vals), key=vals.count)

    problems = []
    for r in rows:
        if r.get("failed"):
            problems.append(f"{os.path.basename(r['page'])}: measurement failed")
            continue
        doc = "resume_full" in r["page"]
        seq = [(n, r["sizes"][n]) for n in HIERARCHY if isinstance(r["sizes"].get(n), (int, float))]
        for i in range(len(seq) - 1):
            a, av = seq[i]
            b, bv = seq[i + 1]
            if av < bv:
                # the hero name is display type above the sections, not a heading
                if not (a == "display" and b == "h2"):
                    problems.append(f"{os.path.basename(r['page'])}: {a} ({av}) is smaller than {b} ({bv})")
            step = av / bv if bv else 0
            skipped = HIERARCHY.index(b) - HIERARCHY.index(a) > 1
            if skipped:
                # No level between them on this page (it has no section
                # headings at all), so this is the title-to-content jump:
                # a wider bound applies and the flat rule does not.
                if step > 2.5:
                    problems.append(
                        f"{os.path.basename(r['page'])}: {a}->{b} is {step:.2f}x across a skipped level"
                    )
                continue
            if a == "display":
                continue  # hero display type: not a heading step
            if 1.0 <= step < 1.08 and b != "body":
                problems.append(f"{os.path.basename(r['page'])}: step {a}->{b} is {step:.2f}x, too flat to read as hierarchy")
            if step > 1.6:
                problems.append(f"{os.path.basename(r['page'])}: step {a}->{b} is {step:.2f}x, a jump that reads as a mistake")
        for n in names:
            v = r["sizes"].get(n)
            if not isinstance(v, (int, float)) or n not in ref:
                continue
            if doc and n in ("h1", "h2", "h3"):
                continue  # the printable document scales its own sections
            if abs(v - ref[n]) > 0.01:
                problems.append(f"{os.path.basename(r['page'])}: {n} is {v} but the site uses {ref[n]}")

    print()
    print("site-wide type scale:")
    for n in names:
        if n in ref:
            print(f"  {n:<10} {ref[n]:>6.1f}px")
    steps = []
    for i in range(len(HIERARCHY) - 1):
        a, b = HIERARCHY[i], HIERARCHY[i + 1]
        if ref.get(a) and ref.get(b):
            steps.append(f"{a}->{b} {ref[a] / ref[b]:.2f}x")
    print("  steps: " + ", ".join(steps))
    print()
    if problems:
        print(f"{len(problems)} font progression problem(s):")
        for line in problems:
            print("  " + line)
    else:
        print(f"{len(rows)} pages, one font progression")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
