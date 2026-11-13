#!/usr/bin/env python3
"""
site_nav.py — post-build step for nabiwiki (run by build.sh after Quartz and site_notice.py).

Adds three things to the generated HTML in public/, without touching the notes:

1. A "Contents" sidebar, replacing Quartz's alphabetical Explorer. It mirrors The Sīrah.md: every
   `##` heading of the hub is a section, every `###` heading a sub-section, and every bullet's first
   wikilink an entry, in the hub's order. Only the section holding the current page is open; it shows
   the page (in a bordered pill) and a few neighbours either side, with a "Show all N…" button.
   Editing the hub changes the sidebar on the next build.
2. An infobox at the top of each note, built from its frontmatter (date, location, commanders… for an
   event; kunyah, clan, death… for a person), with the note's role tags as links to their tag pages.
   It replaces Quartz's raw "Properties" table.
3. Before / after cards on every event in the hub's chronological index, in hub order.
4. The page header, rebuilt to the design in docs/design: breadcrumb (hub › section), title with its
   Arabic name beside it, the epithet line and the notice, in that order. The note's own `# Title (Arabic)`
   heading and epithet line are moved up into it. The infobox is placed after the lead paragraph.

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


NEIGHBOURS = 3           # entries shown either side of the current page in the open section
TRIM_OVER = 2 * NEIGHBOURS + 2


def _list_html(entries, linker, current_slug, depth):
    """<ul> for one run of hub entries. In the section holding the current page a long list is trimmed
    to the page and its neighbours; the rest carry `sn-far` and a button reveals them."""
    slugs = [linker.slug(t) for t, _ in entries]
    here = slugs.index(current_slug) if current_slug in slugs else None
    trim = here is not None and len(entries) > TRIM_OVER
    items = []
    for i, ((target, label), slug) in enumerate(zip(entries, slugs)):
        lab = _emph(html.escape(label))
        classes = []
        if trim and abs(i - here) > NEIGHBOURS:
            classes.append("sn-far")
        if not slug:
            classes.append("sn-missing")
            items.append(f'<li class="{" ".join(classes)}">{lab}</li>')
            continue
        cur = ' class="sn-active" aria-current="page"' if slug == current_slug else ""
        cls = f' class="{" ".join(classes)}"' if classes else ""
        items.append(f'<li{cls}><a{cur} href="{linker.href(slug, depth)}">{lab}</a></li>')
    more = ""
    if trim:
        more = ('<li class="sn-more"><button type="button" class="sn-showall" aria-expanded="false">'
                f'Show all {len(entries)}…</button></li>')
    ul_cls = ' class="sn-trim"' if trim else ""
    return f'<ul{ul_cls}>{"".join(items)}{more}</ul>'


NAV_SCRIPT = (
    "<script>document.addEventListener('click',function(e){"
    "var b=e.target.closest&&e.target.closest('.sn-showall');"
    "if(b){var ul=b.closest('ul');ul.classList.add('sn-expanded');b.parentNode.remove();return}"
    "var m=e.target.closest&&e.target.closest('.sn-menu');"
    "if(m){var o=document.body.classList.toggle('sn-menu-open');m.setAttribute('aria-expanded',o)}"
    "})</script>"
)
MENU_BUTTON = ('<button type="button" class="sn-menu" aria-label="Contents" aria-expanded="false">'
               '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 18 18" fill="none" '
               'stroke="currentColor" stroke-width="1.5"><path d="M3 5h12M3 9h12M3 13h12"></path></svg></button>')


def sidebar_html(sections, linker, current_slug, depth):
    parts = [f'<nav class="sirah-nav" {MARK} aria-label="Contents"><div class="sn-title">Contents</div>']
    for label, target in (("Start here", HOME), ("Full index", HUB)):
        slug = linker.slug(target)
        if slug:
            cur = ' class="sn-hub sn-active" aria-current="page"' if slug == current_slug else ' class="sn-hub"'
            parts.append(f'<a{cur} href="{linker.href(slug, depth)}">{label}</a>')
    for sec in sections:
        slugs_in = {linker.slug(t) for sub in sec["subs"] for t, _ in sub["entries"]}
        open_ = " open" if current_slug in slugs_in else ""
        parts.append(f'<details class="sn-sec"{open_}><summary>{html.escape(sec["title"])}</summary>')
        for sub in sec["subs"]:
            ul = _list_html(sub["entries"], linker, current_slug, depth)
            if sub["title"] and len(sec["subs"]) > 1:
                sub_open = " open" if current_slug in {linker.slug(t) for t, _ in sub["entries"]} else ""
                parts.append(f'<details class="sn-sub"{sub_open}><summary>{html.escape(sub["title"])}</summary>{ul}</details>')
            else:
                parts.append(ul)
        parts.append("</details>")
    parts.append("</nav>")
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
    def card(i, before):
        if i < 0 or i >= len(chrono):
            return ""
        slug = linker.slug(chrono[i])
        if not slug:
            return ""
        label = "← Before" if before else "After →"
        cls = "sn-prev" if before else "sn-next"
        return (f'<a class="{cls}" href="{linker.href(slug, depth)}">'
                f'<span class="sn-seq-label">{label}</span>{html.escape(chrono[i])}</a>')
    return (f'<nav class="sn-seq" {MARK} aria-label="Chronology">{card(idx - 1, True)}{card(idx + 1, False)}</nav>')


# ════════════════════════════════════════════════════════════════════════════════════════════════════

LEFT_OPEN = re.compile(r'<div class="left sidebar"[^>]*>')
CENTER = '<div class="center">'
ARTICLE_ANCHOR = '<div class="markdown-preview-view markdown-rendered">'
NOTICE_RE = re.compile(r'<div class="nw-notice"[^>]*data-nabiwiki-notice[^>]*>.*?</div>', re.S)
CRUMBS_RE = re.compile(r'<nav class="breadcrumb-container".*?</nav>', re.S)
TITLE_RE = re.compile(r'(<h1 class="article-title"[^>]*>)(.*?)(</h1>)', re.S)
BODY_H1_RE = re.compile(r'<h1 id="([^"]*)">(.*?)</h1>\s*', re.S)
EPITHET_RE = re.compile(r'\s*<p>(<em>(?:(?!</em>).)*</em>(?:<sup>.*?</sup>)*)</p>', re.S)
ARABIC_TAIL = re.compile(r'\s*\(([\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\s]+)\)\s*$')
PLAIN_PAGES = {"start-here", "index"}      # the homepage keeps its own heading
TOC_HEAD = "<h3>Table of Contents</h3>"


def section_of(slug, sections, linker):
    for sec in sections:
        if slug in {linker.slug(t) for sub in sec["subs"] for t, _ in sub["entries"]}:
            return sec["title"]
    return None


def restructure(page, slug, sections, linker, depth):
    """Rebuild the page header: breadcrumb (hub › section), title + Arabic, epithet, notice."""
    m_article = page.find(ARTICLE_ANCHOR)
    mt = TITLE_RE.search(page)
    if m_article < 0 or not mt:
        return page
    body = page[m_article:]
    h1 = BODY_H1_RE.search(body)
    arabic, epithet, h1_id = "", "", None
    if h1:
        h1_id = h1.group(1)
        am = ARABIC_TAIL.search(re.sub(r"<a [^>]*>.*?</a>", "", h1.group(2), flags=re.S))
        arabic = am.group(1).strip() if am else ""
        rest = body[h1.end():]
        em = EPITHET_RE.match(rest)
        if em:
            epithet = f'<p class="nw-epithet">{em.group(1)}</p>'
            body = body[:h1.start()] + rest[em.end():]
        else:
            body = body[:h1.start()] + rest
    notice = ""
    nm = NOTICE_RE.search(body)
    if nm:
        notice = nm.group(0)
        body = body[:nm.start()] + body[nm.end():]
    page = page[:m_article] + body
    # title with the Arabic name beside it
    ar = f' <span class="nw-arabic" lang="ar" dir="rtl">{html.escape(arabic)}</span>' if arabic else ""
    page = page[:mt.start()] + mt.group(1) + mt.group(2) + ar + mt.group(3) + page[mt.end():]
    # breadcrumb: hub › section
    hub_slug = linker.slug(HUB)
    crumbs = ""
    if hub_slug and slug != hub_slug:
        sec = section_of(slug, sections, linker)
        crumbs = f'<a href="{linker.href(hub_slug, depth)}">The Sīrah</a>'
        if sec:
            crumbs += f' <span aria-hidden="true">›</span> <span>{html.escape(sec)}</span>'
    crumb_html = f'<nav class="nw-crumbs" aria-label="Breadcrumb">{crumbs}</nav>' if crumbs else ""
    page = CRUMBS_RE.sub(crumb_html, page, count=1) if CRUMBS_RE.search(page) else page.replace(mt.group(1), crumb_html + mt.group(1), 1)
    # epithet and notice directly after the title
    mt = TITLE_RE.search(page)
    page = page[:mt.end()] + epithet + notice + page[mt.end():]
    # the note's own heading is gone: drop its entry from "On this page"
    if h1_id:
        page = re.sub(r'<li class="depth-0"><a href="#' + re.escape(h1_id) + r'".*?</li>', "", page, count=1, flags=re.S)
    return page.replace(TOC_HEAD, "<h3>On this page</h3>")


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
                page = page[:close] + sidebar_html(sections, linker, slug, depth) + NAV_SCRIPT + page[close:]
                page = LEFT_OPEN.sub(lambda m: m.group(0) + MENU_BUTTON, page, count=1)
                stats["sidebar"] += 1
            src = file_of_slug.get(slug)
            note = linker.notes.get(src[:-3]) if src else None
            if note and ARTICLE_ANCHOR in page and slug not in PLAIN_PAGES:
                page = restructure(page, slug, sections, linker, depth)
            if note and ARTICLE_ANCHOR in page and src[:-3] != HUB:
                # 2. infobox: before the lead paragraph (a phone moves it after, see custom.scss)
                box = infobox_html(note, linker, depth)
                lead = re.search(r"<p>", page[page.index(ARTICLE_ANCHOR):])
                if box and lead:
                    at = page.index(ARTICLE_ANCHOR) + lead.start()
                    page = page[:at] + box + '<p class="sn-lead">' + page[at + 3:]
                    stats["infobox"] += 1
                elif box:
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
