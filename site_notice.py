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

import json
import os
import re
import sys

MARK = 'data-nabiwiki-notice="unverified"'

ENTRY_TITLE = "Not yet checked by a person."
ENTRY_TEXT = "This entry was written from the cited pages and is awaiting review against the books."
HUB_TITLE = "Work in progress."
HUB_TEXT = (
    "Entries are being checked one by one against the books they cite; "
    "pages marked “Not yet checked by a person” are still awaiting review."
)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ANCHOR = '<div class="markdown-preview-view markdown-rendered">'


ICON = ('<svg class="nw-notice-icon" aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" '
        'stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6.5"></circle><path d="M8 4.5v4M8 11v.5"></path></svg>')


def callout(title, text):
    """One slim bordered box (styled in custom.scss); site_nav.py moves it under the title block."""
    return (f'<div class="nw-notice" role="note" {MARK}>{ICON}'
            f'<span><strong>{title}</strong> {text}</span></div>')


def is_hub(fname):
    base = os.path.basename(fname).lower()
    return base in ("index.html", "start-here.html") or (base.startswith("the-s") and base.endswith("rah.html"))


def unverified_slugs(public):
    """Slugs of the pages whose note carries the `unverified` tag (the tag list is no longer on the page)."""
    from audit import load_notes
    notes, _ = load_notes()
    with open(os.path.join(public, "static", "contentIndex.json"), encoding="utf-8") as f:
        index = json.load(f)
    out = set()
    for slug, meta in index.items():
        fp = meta.get("filePath") or ""
        note = notes.get(fp[:-3]) if fp.endswith(".md") else None
        if note and "unverified" in (note["fm"].get("tags") or []):
            out.add(slug)
    return out


def main(public):
    marked = skipped = 0
    unv = unverified_slugs(public)
    for root, _, files in os.walk(public):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as f:
                html = f.read()
            if MARK in html or ANCHOR not in html:
                continue
            slug = os.path.relpath(path, public)[:-5].replace(os.sep, "/")
            if slug not in unv and not is_hub(path):
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
