# Site build, navigation and search

Read this before changing `build.sh`, `quartz.config.yaml`, `patch-quartz.mjs`, `custom.scss`, the `site_*.py`
scripts or `site_search.json`. It is not needed for writing or rewriting notes; the rules for those are in
`CLAUDE.md` / `GEMINI.md`.

## Build and deployment

Pushing to `main` runs `.github/workflows/deploy.yml`, which runs `build.sh`. `build.sh` begins with
`python3 audit.py --no-content` under `set -e`: **a citation to a page that does not exist, an orphaned
note, or a wrapped link fails the build, so nothing is deployed** and the live site stays as it was . It then fetches Quartz into `.quartz/` **at the commit pinned as `QUARTZ_REF` in `build.sh`**, copies in
`quartz.config.yaml` and `custom.scss`, runs `patch-quartz.mjs` (folds IJMES diacritics and Arabic script
into ASCII URL slugs — without it the CDN produces redirect loops and 404s — and makes search fold
diacritics; see **Search and names**), builds into `public/`, and
runs `site_notice.py` over `public/` (every page whose note is tagged `unverified` gets a warning callout
under its tags; the homepage gets a site-wide version), then runs `site_nav.py` and `site_search.py` over `public/`, and copies `start-here.html` to `index.html`, so the short start page
is the homepage and the hub stays at `/the-sirah`; then the workflow uploads `public/` as a GitHub Pages artifact and deploys it (Settings → Pages → Source must be "GitHub Actions"; the repo is `eahmed234/eahmed234.github.io`, so the site is served from the root). The notice lives only in the built HTML — notes are
never edited for it — so it disappears from a page as soon as the user marks the note `verified`.
**Site navigation is driven by the hub and frontmatter** (`site_nav.py`; Quartz's Explorer and
Properties plugins are disabled in its favour). The left sidebar mirrors `The Sīrah.md` — its `##`
sections, `###` subsections and the first wikilink of each bullet, in hub order — so reordering or
regrouping the hub reorders the sidebar. Every typed note gets an infobox built from its frontmatter
(fields per `type` are listed in `FIELDS` in `site_nav.py`; a key not listed there is simply not shown) with
role tags (`badri`, `ansari`, `ghazwah`, …) as chips linking to tag pages. Event notes listed under the hub's
*Chronological Master Index* get previous/next links in that order. Like the notice, all of this exists only
in the built HTML.
Anything that must not be published goes in `ignorePatterns` in `quartz.config.yaml` (`sources`,
`review`, `audit.py`, the agent docs, …).

## Search and names

A reader types "Abu Bakr", "Omar" or "Battle of Uhud", not IJMES. Three pieces make that work, none of
which touches a note:

- **`patch-quartz.mjs`, section 5** rewrites Quartz's search script: diacritics, ʿayn and hamzah are
  folded and punctuation splits words ("khattab" finds *al-Khaṭṭāb*), in the index, the query and the
  result snippet alike; and a third field, `names`, is searched and ranked with the title. Each edit must
  match Quartz's built file exactly, and **the build fails if one does not** — which is why Quartz is
  pinned. To upgrade Quartz: raise `QUARTZ_REF`, delete `.quartz/`, build, and try the search.
- **`site_search.py`** (after the build) writes each note's other names into the search index as
  `otherNames`: its frontmatter `aliases` and `arabic`, the names under `extra` in `site_search.json`,
  rule-made English forms (*Ghazwat/Sariyyat X* → "Expedition of X", *Sūrat* → "Surah", *Jabal* → "Mount",
  *Banū* → "Bani / Tribe of") and common spellings of the title (ibn/bin, Zaid, Saad, Waleed). It drops
  tag pages and `.base` files from the index, orders notes by inbound links, writes a redirect for every
  extra name, and settles shared names (below). It also deletes the redirect Quartz writes at a note's
  unfolded name when that differs from the page only in letter case (`Badr.html` → `badr`,
  `Start-Here.html` → `start-here`): a case-insensitive host or file system answers such a redirect for the page itself and the browser loops for ever. GitHub Pages is case-sensitive, so the deletion is a precaution. It then checks every query under `expect` and exits
  non-zero — failing the build — if one no longer matches its note.
- **`site_search.json`** is the only hand-kept part: `extra` (note → names a reader may type), `primary`
  (shared name → the one note its URL opens), `ambiguous` (shared names that become a disambiguation
  page), `expect` (query → note). Its names are finding aids, not content: they appear in no note, so the
  sourcing rules do not govern them — keep them to standard English names and spellings, and add no
  claims. Copy note titles from the file names.

**Shared names.** A kunyah or title often belongs to several people (*Abū ʿAbdillāh* is on fifteen notes).
Quartz would send `/abu-abdillah` to whichever it met first — `/abu-bakr` used to open ʿAbdullāh b.
al-Zubayr. `audit.py` therefore **fails when a name (alias or extra name) is claimed by two notes, or is
another note's title, unless `site_search.json` settles it**. When that happens, do not delete the alias:
add the name to `ambiguous`, or to `primary` if one bearer is plainly the one meant.
