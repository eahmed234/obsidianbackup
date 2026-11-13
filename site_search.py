#!/usr/bin/env python3
"""
site_search.py — post-build step for nabiwiki (run by build.sh after site_nav.py).

Makes the published site findable by a reader who types plain English — "Abu Bakr", "Omar",
"Battle of Uhud" — without touching the notes. It works on the generated files in public/:

1. Search index (static/contentIndex.json). Each note's entry gets an `otherNames` field listing its
   other names: its own aliases and Arabic name, the extra names in site_search.json, a few rule-made
   English forms ("Expedition of …", "Surah …", "Mount …") and common spellings (ibn/bin, Zaid for
   Zayd, Saad for Saʿd, Waleed for Walīd). Tag pages and Obsidian .base files are dropped from the
   index, and notes are ordered by how many other notes link to them, so that between two equally
   good matches the better-known page comes first.
   (Folding of diacritics — "abu" matching "Abū" — and the indexing of `otherNames` as a field ranked
   with the title are done in the search script itself; see section 5 of patch-quartz.mjs.)
2. Redirects. Every extra name gets a redirect page (/omar → ʿUmar b. al-Khaṭṭāb). A name several
   notes share goes to the note site_search.json calls "primary", or becomes a disambiguation page
   if it is listed as "ambiguous". Quartz would otherwise send it to whichever note it met first.
   Redirects that differ from the page they point to only in letter case (Badr.html → badr) are
   removed: on a case-insensitive host or file system such a redirect loops for ever.
3. A check: every query under "expect" in site_search.json must match its note, and the search
   script must carry the folding patch. If not, this script exits non-zero and the build fails.

Usage: python3 site_search.py [public_dir]      (default: public)
"""

import glob
import html
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from audit import load_notes, load_search_config, name_claims, note_aliases, slugify  # noqa: E402

FOLD_MARK = "__nwTok"          # defined by section 5 of patch-quartz.mjs
ARABIC = re.compile(r"[؀-ۿ]")

# Title prefix → English forms a reader may type. "{}" is the rest of the title.
PREFIX_FORMS = [
    ("Ghazwat ", ["Expedition of {}"]),
    ("Sariyyat ", ["Expedition of {}"]),
    ("Sūrat ", ["Surah {}"]),
    ("Banū ", ["Bani {}", "Tribe of {}"]),
    ("Jabal ", ["Mount {}"]),
    ("Wafd ", ["Delegation of {}"]),
    ("Khilāfat ", ["Caliphate of {}"]),
]


# ── folding: a Python copy of __nwFold / __nwTok in patch-quartz.mjs — keep the two in step ──────

def fold(s):
    out = []
    for ch in unicodedata.normalize("NFD", s):
        k = ord(ch)
        if (768 <= k <= 879 or 697 <= k <= 703 or k in (8216, 8217, 39, 96)
                or 1611 <= k <= 1631 or k in (1648, 1600)):
            continue
        out.append(ch)
    return "".join(out).lower()


def tokens(s):
    out = []
    for ch in fold(s):
        k = ord(ch)
        sep = ((k < 128 and not (48 <= k <= 57 or 97 <= k <= 122)) or 8192 <= k <= 8303
               or k in (171, 187, 183, 1548, 1563, 1567, 65018))
        out.append(" " if sep else ch)
    return "".join(out).split()


def matches(query, text):
    """Every token of the query begins some token of the text — FlexSearch 'forward' matching."""
    have = tokens(text)
    return all(any(t.startswith(q) for t in have) for q in tokens(query))


# ── other names of a note ─────────────────────────────────────────────────────────────────────

def spellings(name):
    """Common romanisations of a strictly transliterated name."""
    forms = {name}
    if " b. " in name:
        forms |= {name.replace(" b. ", " ibn "), name.replace(" b. ", " bin ")}
    for f in list(forms):
        forms.add(re.sub(r"ay(?=[^aeiouāīūy])", "ai", f))          # Zayd → Zaid, Quraysh → Quraish
        forms.add(f.replace("aʿ", "aa"))                            # Saʿd → Saad, Kaʿb → Kaab
        forms.add(re.sub(r"ī(?=[a-zḥṣḍṭẓ])", "ee", f).replace("ū", "oo"))   # Walīd → Waleed, Rasūl → Rasool
    return forms


def other_names(title, note, cfg):
    """(names to show, further spellings), each without duplicates and without the title itself."""
    shown = list(note_aliases(note))
    arabic = note["fm"].get("arabic")
    if isinstance(arabic, str) and arabic.strip():
        shown.append(arabic.strip())
    shown += cfg["extra"].get(title, [])
    for prefix, forms in PREFIX_FORMS:
        if title.startswith(prefix):
            shown += [f.format(title[len(prefix):]) for f in forms]
    seen, names = {fold(title)}, []
    for n in shown:
        if fold(n) not in seen:
            seen.add(fold(n)); names.append(n)
    extra = []
    for f in sorted(spellings(title)):          # of the title only: the aliases would triple the index
        if fold(f) not in seen:
            seen.add(fold(f)); extra.append(f)
    return names, extra


def names_line(title, note, cfg):
    names, extra = other_names(title, note, cfg)
    return "; ".join(names + extra)


# ── 1. search index ───────────────────────────────────────────────────────────────────────────

def rewrite_index(public, notes, cfg):
    path = os.path.join(public, "static", "contentIndex.json")
    with open(path, encoding="utf-8") as f:
        index = json.load(f)
    slug_of = {}
    for slug, e in index.items():
        fp = e.get("filePath", "")
        if fp.endswith(".md") and fp[:-3] in notes and "/" not in slug:
            slug_of[fp[:-3]] = slug
    inbound = {s: 0 for s in slug_of.values()}
    for slug, e in index.items():
        for t in set(e.get("links", [])):
            if t in inbound and t != slug:
                inbound[t] += 1
    out, lines = {}, {}
    for title, slug in sorted(slug_of.items(), key=lambda kv: (-inbound[kv[1]], kv[1])):
        e = dict(index[slug])
        lines[title] = names_line(title, notes[title], cfg)
        e["otherNames"] = lines[title]               # indexed as the "names" field (patch-quartz.mjs, 5)
        out[slug] = e
    dropped = len(index) - len(out)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    return slug_of, lines, dropped


# ── 2. redirects and disambiguation pages ─────────────────────────────────────────────────────

def redirect_html(target):
    t = html.escape(target, quote=True)
    return ("<!DOCTYPE html>\n<html lang=\"en-us\">\n<head>\n"
            f"<title>{t}</title>\n<link rel=\"canonical\" href=\"./{t}\">\n"
            "<meta name=\"robots\" content=\"noindex\">\n<meta charset=\"utf-8\">\n"
            f"<meta http-equiv=\"refresh\" content=\"0; url=./{t}\">\n</head>\n</html>\n")


def epithet(note):
    m = re.search(r"^\*([^*\n]+)\*\s*$", note["body"], re.M)
    return m.group(1).strip() if m else ""


def disambiguation_html(public, name, owners, notes, slug_of):
    items = "".join(
        f'<li><a class="internal" href="./{html.escape(slug_of[b], quote=True)}">{html.escape(b)}</a>'
        + (f" — <em>{html.escape(epithet(notes[b]))}</em>" if epithet(notes[b]) else "") + "</li>"
        for b in sorted(owners) if b in slug_of)
    body = (f"<h1>{html.escape(name)}</h1><p>This name is shared by {len(owners)} entries on nabiwiki:</p>"
            f"<ul>{items}</ul><p><a href=\"./\">Return to the index</a></p>")
    title = f"<title>{html.escape(name)} (disambiguation) | nabiwiki</title>"
    tpl_path = os.path.join(public, "404.html")
    if os.path.exists(tpl_path):
        with open(tpl_path, encoding="utf-8") as f:
            tpl = f.read()
        art = re.search(r'(<article class="popover-hint">).*?(</article>)', tpl, re.S)
        if art and "<title>" in tpl:
            page = tpl[:art.start()] + art.group(1) + body + art.group(2) + tpl[art.end():]
            page = re.sub(r"<title>.*?</title>", lambda _: title + '<meta name="robots" content="noindex"/>',
                          page, count=1, flags=re.S)
            return page.replace('data-slug="404"', 'data-slug="disambiguation"', 1)
    return (f"<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\"/>{title}"
            f"<meta name=\"robots\" content=\"noindex\"/></head><body>{body}</body></html>\n")


def is_redirect(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return 'http-equiv="refresh"' in f.read(2000)


def write_redirects(public, notes, cfg, slug_of):
    claims = name_claims(notes, cfg)
    primary = {slugify(k): v for k, v in cfg["primary"].items()}
    stats = {"redirect": 0, "primary": 0, "disambiguation": 0, "skipped": []}
    for sl, owners in sorted(claims.items()):
        owners = {b: n for b, n in owners.items() if b in slug_of}
        if not owners:
            continue
        path = os.path.join(public, sl + ".html")
        if os.path.exists(path) and not is_redirect(path):
            stats["skipped"].append(sl)          # a real page has this address
            continue
        if len(owners) == 1:
            if not os.path.exists(path):
                (b,) = owners
                with open(path, "w", encoding="utf-8") as f:
                    f.write(redirect_html(slug_of[b]))
                stats["redirect"] += 1
        elif primary.get(sl) in owners:
            with open(path, "w", encoding="utf-8") as f:
                f.write(redirect_html(slug_of[primary[sl]]))
            stats["primary"] += 1
        else:
            name = next(iter(owners.values()))
            with open(path, "w", encoding="utf-8") as f:
                f.write(disambiguation_html(public, name, owners, notes, slug_of))
            stats["disambiguation"] += 1
    return stats


def drop_case_twins(public):
    """Quartz writes a redirect at each note's unfolded name (Abū-Bakr-al-Ṣiddīq.html → abu-bakr-al-siddiq).
    For a title that is already plain ASCII the two differ only in letter case (Badr.html → badr,
    Start-Here.html → start-here). A case-insensitive host or file system answers such a redirect for
    the page itself and the browser loops for ever. Remove every redirect whose lower-cased name is a
    real page. Returns the names removed."""
    removed = []
    for root, _, files in os.walk(public):
        have = set(files)
        for name in sorted(files):
            if not name.endswith(".html") or name.lower() == name or name.lower() not in have:
                continue
            path, twin = os.path.join(root, name), os.path.join(root, name.lower())
            if os.path.samefile(path, twin):          # a case-insensitive disk: one file, nothing to do
                continue
            if is_redirect(path) and not is_redirect(twin):
                os.remove(path)
                removed.append(name)
    return removed


# ── 3. check ──────────────────────────────────────────────────────────────────────────────────

def check(public, notes, cfg, lines):
    problems = []
    # Quartz emits the search script as postscript-*.js or as static/scripts/script-*.js
    scripts = glob.glob(os.path.join(public, "**", "*.js"), recursive=True)
    if not any(FOLD_MARK in open(p, encoding="utf-8", errors="replace").read() for p in scripts):
        problems.append("the search script does not carry the folding patch (patch-quartz.mjs, section 5): "
                        "plain spellings such as “Abu Bakr” will not match")
    for query, title in cfg["expect"].items():
        if title not in notes or title not in lines:
            problems.append(f"expect: {query!r} → {title!r}, which is not a published note")
        elif not (matches(query, notes[title]["fm"].get("title", title)) or matches(query, lines[title])):
            problems.append(f"expect: {query!r} does not match [[{title}]] by its title or other names — "
                            f"add the name to \"extra\" in site_search.json")
    return problems


def main(public):
    notes, _ = load_notes()
    cfg = load_search_config()
    slug_of, lines, dropped = rewrite_index(public, notes, cfg)
    stats = write_redirects(public, notes, cfg, slug_of)
    twins = drop_case_twins(public)
    print(f"Search: other names added to {sum(1 for v in lines.values() if v)} of {len(lines)} index entries; "
          f"{dropped} tag/.base entries dropped; {stats['redirect']} new redirects, "
          f"{stats['primary']} shared names sent to their primary note, "
          f"{stats['disambiguation']} disambiguation pages.")
    if twins:
        print(f"  {len(twins)} redirects differing from their page only in letter case removed "
              f"(they loop on case-insensitive hosts): {', '.join(twins[:6])}{' …' if len(twins) > 6 else ''}")
    if stats["skipped"]:
        print(f"  (not redirected, the address is a real page: {', '.join(stats['skipped'])})")
    problems = check(public, notes, cfg, lines)
    if problems:
        print(f"Search check FAILED ({len(problems)}):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"Search check passed ({len(cfg['expect'])} expected queries).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "public"))
