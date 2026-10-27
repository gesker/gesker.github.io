#!/usr/bin/env python3
"""Point the built 404 page at the canonical domain, not at site-url.

mdbook's `input-404` emits `<base href="{site-url}">`, and site-url here is
`https://gesker.github.io` because that is what GitHub Pages needs to publish a
custom domain. Served from https://dennis.gesker.com, that base sends the 404
page's stylesheet requests to the github.io host: a cross-host dependency that
breaks if the custom domain is ever the only host, and it silently serves
whatever CSS is deployed there rather than the CSS in this build.

Usage:
    python3 scripts/fix_404_base.py result            # rewrite result/404.html
    python3 scripts/fix_404_base.py result --check    # exit 1 if it is wrong
"""

import re
import sys

CANONICAL = "https://dennis.gesker.com"


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    path = argv[1].rstrip("/") + "/404.html"
    check = "--check" in argv
    try:
        html = open(path, encoding="utf-8", errors="replace").read()
    except FileNotFoundError:
        sys.exit(f"no 404 page at {path} -- build first")

    m = re.search(r'<base href="([^"]*)"', html)
    if not m:
        print(f"{path}: no <base> tag, nothing to do")
        return 0
    current = m.group(1)
    if current.rstrip("/") == CANONICAL:
        print(f"{path}: base is {current} (canonical)")
        return 0
    if check:
        print(f"{path}: base is {current}, expected {CANONICAL}")
        return 1
    html = html.replace(f'<base href="{current}"', f'<base href="{CANONICAL}"')
    open(path, "w").write(html)
    print(f"{path}: base {current} -> {CANONICAL}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
