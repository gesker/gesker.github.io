#!/usr/bin/env python3
"""Measure vertical spacing and line spacing across the built book.

Serves ./result with a measuring script injected into every page, drives headless
Chrome over the pages, and reports:

  * the type scale: font size, line-height in px and as a ratio, for body copy,
    headings, list items and the small print
  * the space scale: the distinct vertical gaps the page actually renders
  * drift: line-height ratios that disagree between paragraphs and list items,
    gaps that are not on the 4px grid, headings that are tighter or looser than
    the rest

Usage:
    python3 scripts/check_spacing.py [--dir result] [--port 8131] [--json] [pages...]

Exit code is 1 when a problem is found, so it can gate a publish.
"""

import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import urllib.request
from http.server import SimpleHTTPRequestHandler

DEFAULT_PAGES = [
    "about",
    "resume_full",
    "professional",
    "projects",
    "education",
    "certifications",
    "organizations",
    "awards",
    "publications",
    "patents_pending",
    "trademarks",
    "portfolio",
]

CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

PROBE = r"""
<script>
window.addEventListener('load', function () {
  function px(v) { return Math.round(parseFloat(v) * 100) / 100; }
  function info(el) {
    if (!el) return null;
    const cs = getComputedStyle(el);
    const fs = parseFloat(cs.fontSize);
    const lh = cs.lineHeight === 'normal' ? null : parseFloat(cs.lineHeight);
    return {
      fs: px(fs),
      lh: lh === null ? null : px(lh),
      ratio: lh === null ? null : Math.round((lh / fs) * 100) / 100,
      mt: px(cs.marginTop),
      mb: px(cs.marginBottom),
      pt: px(cs.paddingTop),
      pb: px(cs.paddingBottom),
      gap: cs.rowGap === 'normal' ? 0 : px(cs.rowGap)
    };
  }
  // .content wraps <main> and the footer; the page body lives in main, so the
  // gap walk has to happen one level deeper than the wrapper.
  const main = document.querySelector('.content main') || document.querySelector('.content') || document.body;
  const q = s => main.querySelector(s);
  // p.related / .page-badge are 13px secondary text with their own 1.6 rhythm
  const bodyP = main.querySelector('p:not(.related):not(.page-badge):not(.contact-line):not(.resume-toolbar):not([class^="hero-"])');
  const out = { page: location.pathname, sheets: document.styleSheets.length, sel: {}, gaps: [], widths: {} };
  out.cssOk = getComputedStyle(document.documentElement).getPropertyValue('--space-4').trim() !== '';

  [['p','@body'],['li','li'],['h1','h1'],['h2','h2'],['h3','h3'],['h4','h4'],
   ['strong','strong'],['table','table'],['tableCell','td'],
   ['card','.info-card'],['cardItem','.info-grid > li'],['infoTitle','.info-title'],
   ['infoSub','.info-sub'],['infoMeta','.info-meta'],['related','p.related'],
   ['chips','.toc-chips'],['hero','.hero'],['footer','.site-footer']
  ].forEach(function (pair) {
    out.sel[pair[0]] = info(pair[1] === '@body' ? bodyP : q(pair[1]));
  });

  // Every gap between two consecutive block children of .content
  const content = main;
  if (content) {
    const kids = Array.from(content.children).filter(function (el) {
      const cs = getComputedStyle(el);
      return cs.display !== 'none' && el.getBoundingClientRect().height > 0;
    });
    for (let i = 1; i < kids.length; i++) {
      const a = kids[i - 1].getBoundingClientRect();
      const b = kids[i].getBoundingClientRect();
      const g = Math.round(b.top - a.bottom);
      if (g > 0 && g < 200) out.gaps.push({ gap: g, after: kids[i - 1].tagName, before: kids[i].tagName });
    }
  }
  const d = document.createElement('div');
  d.id = 'spacing';
  d.textContent = 'SPACING::' + JSON.stringify(out);
  document.body.appendChild(d);
});
</script>
"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)

    def do_GET(self):
        path = self.path.split("?")[0]
        fs = os.path.join(self.directory, path.lstrip("/"))
        if path.endswith(".html") and os.path.exists(fs):
            body = open(fs, "rb").read().decode("utf-8", "replace")
            data = body.replace("</body>", PROBE + "</body>").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

    def log_message(self, *a):
        pass


class Threaded(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def measure(root, port, page, attempts=3):
    url = f"http://127.0.0.1:{port}/{page}.html"
    # A reused profile serves cached CSS from the previous build and every
    # measurement comes back one edit stale. Fresh profile, every page.
    profile = tempfile.mkdtemp(prefix="spacing-chrome-")
    try:
        with open(os.devnull, "wb") as devnull:
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
                    url,
                ],
                capture_output=True,
                timeout=120,
            ).stdout.decode("utf-8", "replace")
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    m = re.search(r'<div id="spacing">SPACING::(.*?)</div>', html, re.S)
    if not m:
        return None
    import html as htmlmod

    data = json.loads(htmlmod.unescape(m.group(1)))
    # A page that lost its stylesheets is a failed load, not a spacing change:
    # retry before reporting anything, or the whole audit is noise.
    if (not data.get("cssOk", True) or data["sheets"] < 11) and attempts > 1:
        return measure(root, port, page, attempts - 1)
    return data


def main(argv):
    root = "result"
    if "--dir" in argv:
        root = argv[argv.index("--dir") + 1]
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8131
    pages = [a for a in argv[1:] if not a.startswith("--") and a not in (root, str(port))] or DEFAULT_PAGES

    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    handler = lambda *a, **k: Handler(*a, directory=os.path.abspath(root), **k)
    httpd = Threaded(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    results, problems = [], []
    for page in pages:
        r = measure(root, port, page)
        if r is None:
            problems.append(f"{page}: no measurement (page missing or script blocked)")
            continue
        results.append(r)

    httpd.shutdown()

    if "--json" in argv:
        print(json.dumps(results, indent=1))
        return 0

    # --- per page type scale -------------------------------------------------
    print("type scale (page: selector  font / line-height = ratio)")
    keys = ["p", "li", "h1", "h2", "h3", "h4", "infoTitle", "infoSub", "infoMeta", "tableCell"]
    for r in results:
        bits = []
        for k in keys:
            s = r["sel"].get(k)
            if not s:
                continue
            ratio = f"{s['ratio']:.2f}" if s["ratio"] else "-"
            bits.append(f"{k} {s['fs']:g}/{s['lh'] if s['lh'] else '-'}={ratio}")
        print(f"  {r['page']:<24} " + "  ".join(bits))

    # --- drift -------------------------------------------------------------
    for r in results:
        sel = r["sel"]
        p, li = sel.get("p"), sel.get("li")
        if p and li and p["ratio"] and li["ratio"] and abs(p["ratio"] - li["ratio"]) > 0.02:
            problems.append(
                f"{r['page']}: paragraph line-height {p['ratio']} vs list item {li['ratio']}"
            )
        for k in ("p", "li"):
            s = sel.get(k)
            if s and s["ratio"] and not (1.45 <= s["ratio"] <= 1.75):
                problems.append(f"{r['page']}: {k} line-height ratio {s['ratio']} outside 1.45-1.75")
        for k in ("h1", "h2", "h3", "h4"):
            s = sel.get(k)
            if s and s["ratio"] and s["ratio"] > 1.4:
                problems.append(f"{r['page']}: {k} line-height ratio {s['ratio']} too loose for a heading")

    # --- space scale -------------------------------------------------------
    all_gaps = {}
    for r in results:
        for g in r["gaps"]:
            all_gaps[g["gap"]] = all_gaps.get(g["gap"], 0) + 1
    print()
    print("vertical gaps actually rendered (px: count):")
    print("  " + ", ".join(f"{k}:{v}" for k, v in sorted(all_gaps.items())))
    off_grid = sorted(g for g in all_gaps if g % 4 != 0 and all_gaps[g] >= 3)
    if off_grid:
        problems.append(f"gaps off the 4px grid used 3+ times: {off_grid}")
    if len(all_gaps) > 14:
        problems.append(f"{len(all_gaps)} distinct vertical gaps -- the scale is not a scale")

    print()
    if problems:
        print(f"{len(problems)} spacing problem(s):")
        for line in problems:
            print("  " + line)
    else:
        print("spacing and line spacing are consistent")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
