#!/usr/bin/env python3
"""Prove every published page can actually be reached, and nothing is orphaned.

mdBook renders the sidebar from JS, so a page can exist, be listed in SUMMARY.md,
and still have no static `<a href>` pointing at it -- invisible to a crawler that
does not run scripts, and unreachable for a reader who lands on one page.

Two checks, both hard failures:

  1. reachability: walk the anchor graph from index.html; every page must be
     reachable.
  2. in-degree: every page needs at least one inbound static link, so it is
     reachable even if the page you came from gets pruned.

Link resolution is scripts/check_links.py's job; this only asks whether the graph
is connected.

Usage:
    python3 scripts/check_reachable.py ./book
"""

import os
import re
import sys
from collections import deque

# mdBook's helpers and the print-only artifacts are not reader pages.
SKIP = {"print.html", "toc.html", "404.html"}
SKIP_PREFIX = ("resume_short/",)
SKIP_SUFFIX = ("_for_pdf_only.html",)

HREF = re.compile(r'<a\b[^>]*\bhref="([^"]+)"', re.I)
EXTERNAL = ("http://", "https://", "mailto:", "tel:", "javascript:", "data:", "#")


def reader_pages(root):
    pages = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith(".html"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")
            if rel in SKIP or rel.startswith(SKIP_PREFIX) or rel.endswith(SKIP_SUFFIX):
                continue
            # a meta-refresh stub exists to catch a retired URL; nobody should
            # be linking to it, so it is not part of the reader graph
            head = open(os.path.join(dirpath, name), encoding="utf-8", errors="replace").read()
            if re.search(r'http-equiv="refresh"', head, re.I):
                continue
            pages.append(rel)
    return sorted(pages)


def targets(root, rel, known):
    """Local pages this page links to, resolved relative to its own directory."""
    path = os.path.join(root, rel)
    try:
        html = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    out = []
    for raw in HREF.findall(html):
        raw = raw.strip()
        if not raw or raw.startswith(EXTERNAL):
            continue
        raw = raw.split("#", 1)[0].split("?", 1)[0]
        if not raw:
            continue
        if raw.startswith("/"):
            dest = raw.lstrip("/")
        else:
            dest = os.path.normpath(os.path.join(os.path.dirname(rel), raw)).replace(os.sep, "/")
        if dest in ("", "."):
            dest = "index.html"
        if dest in known:
            out.append(dest)
    return out


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    root = argv[1].rstrip("/")
    if not os.path.isdir(root):
        sys.exit(f"{root} is not a directory")

    pages = reader_pages(root)
    if "index.html" not in pages:
        sys.exit(f"no index.html in {root} -- build first")
    known = set(pages)

    edges = {p: targets(root, p, known) for p in pages}
    inbound = {p: 0 for p in pages}
    for src, dests in edges.items():
        for d in dests:
            if d != src:
                inbound[d] += 1

    reachable = {"index.html"}
    queue = deque(["index.html"])
    while queue:
        cur = queue.popleft()
        for nxt in edges[cur]:
            if nxt not in reachable:
                reachable.add(nxt)
                queue.append(nxt)

    orphaned = [p for p in pages if p not in reachable]
    unlinked = [p for p in pages if inbound[p] == 0]

    print(f"{len(pages)} reader pages, {sum(len(v) for v in edges.values())} internal anchor edges")
    for p in pages:
        flag = ""
        if p not in reachable:
            flag = "  UNREACHABLE"
        elif inbound[p] == 0:
            flag = "  no inbound link"
        if flag:
            print(f"  {p:<34} {len(edges[p]):>3} out, {inbound[p]:>3} in{flag}")

    problems = []
    if orphaned:
        problems.append(f"{len(orphaned)} page(s) unreachable from index.html: {', '.join(orphaned)}")
    if unlinked:
        problems.append(f"{len(unlinked)} page(s) with no inbound link: {', '.join(unlinked)}")

    if problems:
        for line in problems:
            print(line)
        return 1
    print("every reader page is reachable and carries an inbound link")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
