#!/usr/bin/env python3
"""
site_notice.py — post-build step for nabiwiki (run by build.sh after Quartz).

Adds a visible notice to every published page whose note is tagged `unverified`, i.e. every entry
the editor has not yet checked against the books it cites. The start page and the hub get a site-wide
version of the notice. The notes themselves are not
touched: the notice is injected into the built HTML in public/, so it disappears from a page as soon
as the note's tag is changed to `verified` and the site is rebuilt.

Usage: python3 site_notice.py [public_dir]      (default: public)
"""

import os
import re
import sys

MARK = 'data-nabiwiki-notice="unverified"'

ENTRY_TITLE = "Unverified entry"
ENTRY_TEXT = (
    "The editor has not yet checked this entry against the books it cites. "
    "Its contents and citations may contain errors; "
    "consult the cited pages before relying on it."
)
HUB_TITLE = "Work in progress"
HUB_TEXT = (
    "Entries on nabiwiki are being checked one by one against the books they cite. "
    "Pages marked “Unverified entry” have not yet been "
    "checked; consult the cited pages before relying on them."
)

TAG_RE = re.compile(r'<ul class="tags"[^>]*>.*?</ul>', re.S)
UNVERIFIED_RE = re.compile(r'href="(?:\./|\.\./)*tags/unverified"')
ANCHOR = '<div class="markdown-preview-view markdown-rendered">'


def callout(title, text):
    return (
        f'<blockquote class="callout warning" data-callout="warning" {MARK}>'
        '<div class="callout-title"><div class="callout-icon"></div>'
        f'<div class="callout-title-inner"><p>{title}</p></div></div>'
        f'<div class="callout-content"><p>{text}</p></div></blockquote>'
    )


def is_hub(fname):
    base = os.path.basename(fname).lower()
    return base in ("index.html", "start-here.html") or (base.startswith("the-s") and base.endswith("rah.html"))


def main(public):
    marked = skipped = 0
    for root, _, files in os.walk(public):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as f:
                html = f.read()
            if MARK in html or ANCHOR not in html:
                continue
            tags = TAG_RE.search(html)
            if not tags or not UNVERIFIED_RE.search(tags.group(0)):
                skipped += 1
                continue
            box = callout(HUB_TITLE, HUB_TEXT) if is_hub(path) else callout(ENTRY_TITLE, ENTRY_TEXT)
            html = html.replace(ANCHOR, ANCHOR + box, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            marked += 1
    print(f"Unverified notice added to {marked} pages ({skipped} content pages without the tag).")
    if marked == 0:
        print("Warning: no page received the notice — has the Quartz markup changed?")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "public")
