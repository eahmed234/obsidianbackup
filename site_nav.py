#!/usr/bin/env python3
"""
site_nav.py — post-build step for nabiwiki (run by build.sh after Quartz and site_notice.py).

Adds three things to the generated HTML in public/, without touching the notes:

1. A "Contents" sidebar, replacing Quartz's alphabetical Explorer. It mirrors The Sīrah.md: every
   `##` heading of the hub is a section, every `###` heading a sub-section, and every bullet's first
   wikilink an entry, in the hub's order. The section holding the current page is open and the page is
   highlighted. Editing the hub changes the sidebar on the next build.
2. An infobox at the top of each note, built from its frontmatter (date, location, commanders… for an
   event; kunyah, clan, death… for a person), with the note's role tags as links to their tag pages.
   It replaces Quartz's raw "Properties" table.
3. Previous / next links on every event in the hub's chronological index, in hub order.

Usage: python3 site_nav.py [public_dir]      (default: public)
"""

import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from audit import load_notes  # noqa: E402  (frontmatter parser and alias map shared with the audit)

HUB = "The Sīrah"
HOME = "Start Here"          # the short start page; build.sh copies it to index.html
CHRONO_HEADING = "Chronological Master Index"
MARK = "data-sirah-nav"

# ── infobox fields: (frontmatter keys, label) in display order, per note type ───────────────────────
FIELDS = {
    "event": [
        (["date_hijri"], "Date"), (["date_gregorian"], "Date (CE)"), (["date_period"], "Period"),
        (["duration"], "Duration"), (["location", "locations"], "Location"),
        (["leader"], "Commander"), (["commanders_muslim"], "Muslim command"),
        (["standard_bearer"], "Standard-bearer"), (["deputy_in_medina", "deputy_medina"], "Deputy in Medina"),
        (["adversaries"], "Opponents"), (["commanders_enemy"], "Opposing command"),
        (["forces_muslim", "strength_muslim"], "Muslim strength"),
        (["forces_enemy", "strength_enemy"], "Opposing strength"),
        (["casualties_muslim"], "Muslim casualties"), (["casualties_enemy"], "Opposing casualties"),
        (["booty", "spoils"], "Spoils"), (["outcome"], "Outcome"),
        (["quranic_references", "quranic_reference"], "Qurʾān"),
    ],
    "person": [
        (["kunya"], "Kunyah"), (["name"], "Name"), (["epithet"], "Epithet"), (["nisbah"], "Nisbah"),
        (["father"], "Father"), (["mother"], "Mother"), (["parents"], "Parents"),
        (["lineage", "nasab"], "Lineage"), (["tribe"], "Tribe"), (["clan"], "Clan"),
        (["confederacy"], "Alliance"), (["birth", "birth_approx"], "Born"),
        (["death", "death_hijri"], "Died"), (["death_place"], "Place of death"), (["burial"], "Burial"),
        (["spouse", "spouses", "matrimony"], "Spouse(s)"), (["children", "son"], "Children"),
        (["siblings", "brother"], "Siblings"), (["relation", "kinship"], "Relation to the Prophet ﷺ"),
        (["role"], "Role"), (["battles"], "Campaigns"),
    ],
    "place": [
        (["location"], "Location"), (["primary_event", "primary_events"], "Events"),
        (["key_landmarks", "key_features", "key_topographical_landmarks"], "Landmarks"),
        (["built_by"], "Built by"),
    ],
    "group": [
        (["lineage"], "Lineage"), (["territory"], "Territory"), (["relation"], "Relation"),
        (["allies"], "Allies"), (["chieftains"], "Chieftains"),
        (["prominent_members", "notable_members", "notables", "notable_figures"], "Notable members"),
        (["primary_event"], "Events"),
    ],
    "text": [
        (["surah_number"], "Sūrah"), (["total_ayahs"], "Āyāt"), (["period"], "Revealed"),
        (["surah_order"], "Order of revelation"), (["primary_event", "primary_events"], "Occasions"),
    ],
}
MAX_VALUE = 260          # longer frontmatter values are prose, not infobox material

# Tags shown in the infobox as linked roles (others stay in Quartz's tag list).
ROLE_TAGS = {
    "ashara_mubashsharah": "The Ten promised Paradise", "ahl_al_bayt": "Ahl al-Bayt",
    "umm_al_muminin": "Mother of the Believers", "badri": "Present at Badr", "muhajir": "Muhājir",
    "ansari": "Anṣārī", "naqib": "Naqīb at al-ʿAqabah", "martyr": "Martyr", "shahid": "Martyr",
    "caliph": "Caliph", "sahabiyyah": "Ṣaḥābiyyah", "early_convert": "Early convert",
    "ghazwah": "Ghazwah", "sariyyah": "Sariyyah", "wufud": "Delegations",
    "makkan_era": "Makkan era", "madinan_era": "Madinan era",
}


# ════════════════════════════════════════════════════════════════════════════════════════════════════
#  Inline markdown → HTML (enough for frontmatter values and hub labels)
# ════════════════════════════════════════════════════════════════════════════════════════════════════

class Linker:
    def __init__(self, public):
        with open(os.path.join(public, "static", "contentIndex.json"), encoding="utf-8") as f:
            index = json.load(f)
        self.slug_of_file = {v.get("filePath"): k for k, v in index.items() if v.get("filePath")}
        self.notes, self.aliases = load_notes()

    def slug(self, target):
        base = self.aliases.get(target.strip())
        return self.slug_of_file.get(f"{base}.md") if base else None

    def href(self, slug, depth):
        return ("../" * depth if depth else "./") + slug


def inline(text, linker, depth):
    """Wikilinks, **bold**, *italic* → HTML; everything else escaped."""
    out, pos = [], 0
    for m in re.finditer(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]", text):
        out.append(_emph(html.escape(text[pos:m.start()])))
        target, label = m.group(1), m.group(2) or m.group(1)
        slug = linker.slug(target)
        lab = _emph(html.escape(label))
        out.append(f'<a class="internal" href="{linker.href(slug, depth)}">{lab}</a>' if slug else lab)
        pos = m.end()
    out.append(_emph(html.escape(text[pos:])))
    return "".join(out)


def _emph(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)


# ════════════════════════════════════════════════════════════════════════════════════════════════════
#  The hub → sidebar structure and chronology
# ════════════════════════════════════════════════════════════════════════════════════════════════════

def clean_heading(h):
    h = re.sub(r"^[^\w*]+", "", h).strip()                    # leading emoji
    h = re.sub(r"\s*\((?:\*[^)]*\*|[؀-ۿ\s]+)[^)]*\)\s*", " ", h)   # (*Arabic term*) / (عربي)
    h = re.sub(r"^\d+\.\s*", "", h)                           # "1. "
    return re.sub(r"\s+", " ", h).strip(" —-")


def parse_hub(linker):
    """[{title, subs: [{title, entries: [(target, label)]}]}], plus the chronological target list."""
    raw = linker.notes[HUB]["raw"]
    sections, chrono, in_chrono = [], [], False
    for line in raw.split("\n"):
        if line.startswith("## "):
            in_chrono = CHRONO_HEADING in line
            sections.append({"title": clean_heading(line[3:]), "subs": [{"title": None, "entries": []}]})
        elif line.startswith("### ") and sections:
            sections[-1]["subs"].append({"title": clean_heading(line[4:]), "entries": []})
        elif re.match(r"^\s*[-*]\s", line) and sections:
            m = re.search(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]", line)
            if not m:
                continue
            target = m.group(1).strip()
            label = (m.group(2) or target).strip()
            sections[-1]["subs"][-1]["entries"].append((target, label))
            if in_chrono:
                chrono.append(target)
    for s in sections:
        s["subs"] = [x for x in s["subs"] if x["entries"]]
    return [s for s in sections if s["subs"]], chrono


def sidebar_html(sections, linker, current_slug, depth):
    parts = [f'<nav class="sirah-nav" {MARK} aria-label="Contents"><details class="sn-root" open>'
             '<summary class="sn-title">Contents</summary>']
    hub_slug = linker.slug(HUB)
    if hub_slug:
        cls = " sn-active" if hub_slug == current_slug else ""
        parts.append(f'<a class="sn-hub{cls}" href="{linker.href(hub_slug, depth)}">Full index</a>')
    home_slug = linker.slug(HOME)
    if home_slug:
        cls = " sn-active" if home_slug == current_slug else ""
        parts.insert(1, f'<a class="sn-hub{cls}" href="{linker.href(home_slug, depth)}">Start here</a>')
    for sec in sections:
        slugs_in = {linker.slug(t) for sub in sec["subs"] for t, _ in sub["entries"]}
        open_ = " open" if current_slug in slugs_in else ""
        parts.append(f'<details class="sn-sec"{open_}><summary>{html.escape(sec["title"])}</summary>')
        for sub in sec["subs"]:
            items = []
            for target, label in sub["entries"]:
                slug = linker.slug(target)
                lab = _emph(html.escape(label))
                if not slug:
                    items.append(f'<li class="sn-missing">{lab}</li>')
                    continue
                cls = ' class="sn-active" aria-current="page"' if slug == current_slug else ""
                items.append(f'<li><a{cls} href="{linker.href(slug, depth)}">{lab}</a></li>')
            ul = f'<ul>{"".join(items)}</ul>'
            if sub["title"] and len(sec["subs"]) > 1:
                sub_open = " open" if current_slug in {linker.slug(t) for t, _ in sub["entries"]} else ""
                parts.append(f'<details class="sn-sub"{sub_open}><summary>{html.escape(sub["title"])}</summary>{ul}</details>')
            else:
                parts.append(ul)
        parts.append("</details>")
    parts.append("</details></nav>")
    # on narrow screens the sidebar sits above the article: start it folded
    parts.append("<script>if(window.innerWidth<800){document.querySelectorAll('.sirah-nav .sn-root')"
                 ".forEach(function(d){d.removeAttribute('open')})}</script>")
    return "".join(parts)


# ════════════════════════════════════════════════════════════════════════════════════════════════════
#  Infobox and chronology links
# ════════════════════════════════════════════════════════════════════════════════════════════════════

def as_list(v):
    if v is None or v == "" or v == []:
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


def infobox_html(note, linker, depth):
    fm = note["fm"]
    ntype = fm.get("type")
    if ntype not in FIELDS:
        return ""
    rows = []
    for keys, label in FIELDS[ntype]:
        for k in keys:
            vals = [v for v in as_list(fm.get(k)) if v.strip() and len(v) <= MAX_VALUE]
            if vals:
                cell = "<br>".join(inline(v, linker, depth) for v in vals)
                rows.append(f"<tr><th>{html.escape(label)}</th><td>{cell}</td></tr>")
                break
    tags = as_list(fm.get("tags"))
    roles = [(t, ROLE_TAGS[t]) for t in tags if t in ROLE_TAGS]
    seen, chips = set(), []
    for t, lab in roles:
        if lab in seen:
            continue
        seen.add(lab)
        chips.append(f'<a class="sn-chip" href="{"../" * depth if depth else "./"}tags/{t}">{html.escape(lab)}</a>')
    if not rows and not chips:
        return ""
    title = html.escape(str(fm.get("title") or ""))
    arabic = html.escape(str(fm.get("arabic") or ""))
    head = f'<div class="sn-ib-title">{title}</div>' + (f'<div class="sn-ib-arabic" dir="rtl" lang="ar">{arabic}</div>' if arabic else "")
    chip_html = f'<div class="sn-chips">{"".join(chips)}</div>' if chips else ""
    return (f'<aside class="sn-infobox" {MARK}>{head}{chip_html}'
            f'<table>{"".join(rows)}</table></aside>')


def sequence_html(chrono, idx, linker, depth):
    def link(i, arrow_first):
        if i < 0 or i >= len(chrono):
            return "<span></span>"
        slug = linker.slug(chrono[i])
        if not slug:
            return "<span></span>"
        name = html.escape(chrono[i])
        inner = f"← {name}" if arrow_first else f"{name} →"
        cls = "sn-prev" if arrow_first else "sn-next"
        return f'<a class="{cls}" href="{linker.href(slug, depth)}">{inner}</a>'
    return (f'<nav class="sn-seq" {MARK} aria-label="Chronology">{link(idx - 1, True)}'
            f'<span class="sn-seq-label">Chronology</span>{link(idx + 1, False)}</nav>')


# ════════════════════════════════════════════════════════════════════════════════════════════════════

LEFT_OPEN = re.compile(r'<div class="left sidebar"[^>]*>')
CENTER = '<div class="center">'
ARTICLE_ANCHOR = '<div class="markdown-preview-view markdown-rendered">'
NOTICE_END = re.compile(r'(<blockquote class="callout warning"[^>]*data-nabiwiki-notice[^>]*>.*?</blockquote>)', re.S)


def main(public):
    linker = Linker(public)
    sections, chrono = parse_hub(linker)
    file_of_slug = {v: k for k, v in linker.slug_of_file.items()}
    chrono_slugs = [linker.slug(t) for t in chrono]
    stats = {"sidebar": 0, "infobox": 0, "sequence": 0}
    for root, _, files in os.walk(public):
        for name in files:
            if not name.endswith(".html"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, public)
            depth = rel.count(os.sep)
            with open(path, encoding="utf-8") as f:
                page = f.read()
            if MARK in page or CENTER not in page:
                continue
            slug = rel[:-5].replace(os.sep, "/")
            # 1. sidebar: at the end of the left column, just before the centre column
            if LEFT_OPEN.search(page):
                i = page.index(CENTER)
                close = page.rfind("</div>", 0, i)
                page = page[:close] + sidebar_html(sections, linker, slug, depth) + page[close:]
                stats["sidebar"] += 1
            src = file_of_slug.get(slug)
            note = linker.notes.get(src[:-3]) if src else None
            if note and ARTICLE_ANCHOR in page and src[:-3] != HUB:
                # 2. infobox: after the unverified notice if there is one, else at the top of the article
                box = infobox_html(note, linker, depth)
                if box:
                    m = NOTICE_END.search(page)
                    if m:
                        page = page[:m.end()] + box + page[m.end():]
                    else:
                        page = page.replace(ARTICLE_ANCHOR, ARTICLE_ANCHOR + box, 1)
                    stats["infobox"] += 1
                # 3. chronology: at the end of the article
                if slug in chrono_slugs and "</article>" in page:
                    seq = sequence_html(chrono, chrono_slugs.index(slug), linker, depth)
                    page = page.replace("</article>", seq + "</article>", 1)
                    stats["sequence"] += 1
            with open(path, "w", encoding="utf-8") as f:
                f.write(page)
    print(f"Navigation: sidebar on {stats['sidebar']} pages, infobox on {stats['infobox']}, "
          f"chronology links on {stats['sequence']}.")
    if not stats["sidebar"]:
        print("Warning: no sidebar was added — has the Quartz markup changed?")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "public")
