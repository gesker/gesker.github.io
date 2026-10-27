#!/usr/bin/env python3
"""Check every internal link in a built mdBook tree.

    python3 scripts/check_links.py ./result

Walks *.html under the given directory, resolves each local href/src against
the file that contains it, and fails when the target is missing or when a
#fragment does not exist in the target document. External links, mailto: and
javascript: are skipped. Exit status 1 on any broken link.
"""
import os
import re
import sys
from urllib.parse import unquote, urlsplit

HREF = re.compile(r'(?:href|src)="([^"]+)"')
ID = re.compile(r'\bid="([^"]+)"')
NAME = re.compile(r'\bname="([^"]+)"')
SKIP_SCHEMES = ("http://", "https://", "mailto:", "javascript:", "data:", "tel:")


def anchors(path):
    """Ids and legacy name anchors available in a target document."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            body = fh.read()
    except OSError:
        return set()
    found = set(ID.findall(body)) | set(NAME.findall(body))
    # mdBook's fragment map redirects old anchors to new ones
    found |= set(re.findall(r'"([^"]+)":"[^"]+"', body))
    return found


def main(root):
    cache = {}
    broken = []
    checked = 0
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith(".html"):
                continue
            page = os.path.join(dirpath, name)
            with open(page, "r", encoding="utf-8", errors="replace") as fh:
                body = fh.read()
            rel_page = os.path.relpath(page, root)
            for raw in HREF.findall(body):
                if not raw or raw.startswith(SKIP_SCHEMES):
                    continue
                parts = urlsplit(raw)
                target_path = unquote(parts.path)
                fragment = unquote(parts.fragment)
                if not target_path and not fragment:
                    continue
                if target_path:
                    if target_path.startswith("/"):
                        resolved = os.path.join(root, target_path.lstrip("/"))
                    else:
                        resolved = os.path.join(dirpath, target_path)
                    resolved = os.path.normpath(resolved)
                    if not os.path.exists(resolved):
                        broken.append((rel_page, raw, "missing file"))
                        continue
                else:
                    resolved = page
                checked += 1
                if fragment and resolved.endswith(".html"):
                    if resolved not in cache:
                        cache[resolved] = anchors(resolved)
                    if fragment not in cache[resolved]:
                        broken.append((rel_page, raw, "missing anchor"))
    print(f"checked {checked} internal links in {root}")
    if broken:
        print(f"BROKEN: {len(broken)}")
        for page, raw, why in broken:
            print(f"  {page}: {raw}  ({why})")
        return 1
    print("all internal links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "result"))
