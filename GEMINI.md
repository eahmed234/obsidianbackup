# GEMINI.md

This file provides guidance to Antigravity (Gemini) when working in this repository.
`CLAUDE.md` carries the same text for Claude; the two are kept identical apart from their first two
lines — **when you change one, change the other**.

## What this repository is

An Obsidian vault, git-backed, containing an English-language scholarly wiki of the *Sīrah* (Prophetic
biography) written from an orthodox Sunni perspective. The deliverable is the Markdown notes and the link
graph between them. The same files are also the source of the public site **nabiwiki**
(https://nabiwiki.netlify.app/), built with Quartz v5.

Layout (repository root):

| Path | What it is |
| --- | --- |
| `*.md` | The notes — **flat in the root, no folders** (~470 as of Nov 2026). `CLAUDE.md`/`GEMINI.md` are not notes. |
| `The Sīrah.md` | The hub (`type: index`) — the only navigational entry point |
| `sources/1693.epub` | *Subul al-Hudā war-Rashād* — the corpus, tracked in git |
| `sources/9767.epub` | *al-Iṣābah fī Tamyīz al-Ṣaḥābah* — the corpus, tracked in git |
| `audit.py` | Integrity checks and source-verification triage (see **Audit tooling**) |
| `site_notice.py` | Post-build step: puts an "Unverified entry" notice on every published page tagged `unverified` |
| `site_nav.py` | Post-build step: Contents sidebar built from the hub, frontmatter infoboxes, chronological prev/next links |
| `review/` | Generated source sheets and triage reports — git-ignored, Quartz-ignored |
| `build.sh`, `quartz.config.yaml`, `patch-quartz.mjs`, `custom.scss`, `netlify.toml`, `.github/` | Site build |
| `.obsidian/` | Obsidian config + `obsidian-git` plugin |

## Git workflow

Commits are normally made by the Obsidian **obsidian-git** plugin:
- Commit message template `vault backup: {{date}}`, format `YYYY-MM-DD HH:mm:ss`.
- Sync method `merge`, `pullBeforePush` on, auto-intervals disabled (manual trigger inside Obsidian).

When committing from the CLI, follow the same `vault backup: <timestamp>` convention. Expect
`.obsidian/workspace.json` and `.obsidian/graph.json` as noise in diffs (both are git-ignored).

## Build and deployment

Pushing to `main` runs `.github/workflows/deploy.yml`, which runs `build.sh`. `build.sh` begins with
`python3 audit.py --no-content` under `set -e`: **a citation to a page that does not exist, an orphaned
note, or a wrapped link fails the build, so nothing is deployed** and the live site stays as it was (this
also gates a Netlify-side build, which uses the same script). It then clones Quartz into `.quartz/`, copies in
`quartz.config.yaml` and `custom.scss`, runs `patch-quartz.mjs` (folds IJMES diacritics and Arabic script
into ASCII URL slugs — without it the CDN produces redirect loops and 404s), builds into `public/`, and
runs `site_notice.py` over `public/` (every page whose note is tagged `unverified` gets a warning callout
under its tags; the homepage gets a site-wide version), then runs `site_nav.py` over `public/`, and copies `the-sirah.html` to `index.html` so the hub
is the homepage; then `netlify-cli` deploys `public/`. The notice lives only in the built HTML — notes are
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

## Architecture of the knowledge graph

**The hub.** `The Sīrah.md` holds the chronological master index of events (Makkan era → early Madinan →
major *ghazawāt* → culmination & departure → the era of the Rightly Guided Caliphs), plus registers for
biographies, Qurʾānic nodes, tribes and clans, geography, and classical authorities. **Every new note must be added to the matching section of the hub**, or it is an
orphan — there is no folder structure to discover it by. `audit.py` fails on orphans.

**Note types** (`type:` in frontmatter; counts as of Nov 2026, they drift):

| `type` | Count | Body pattern |
| --- | --- | --- |
| `person` | 268 | Lead paragraph, then plain-titled chronological sections (Name, early life, campaigns…, Death) |
| `event` | 106 | Numbered sections: context, deployment, climax, aftermath, Qurʾānic connection |
| `group` | 39 | Lineage (*nasab*), territory, alliances (*ḥilf*), role in the Sīrah, members |
| `place` | 36 | Topography, events at the place, linked to its `primary_event` |
| `text` | 20 | Qurʾān sūrahs: overview, then an *asbāb al-nuzūl* table (āyah / Arabic / occasion / persons) |
| `source` | 2 | `Subul al-Hudā war-Rashād.md`, `al-Iṣābah fī Tamyīz al-Ṣaḥābah.md` |
| `index` | 1 | `The Sīrah.md` |

`Ghazwat Badr al-Kubrā.md` and `ʿAbd al-Raḥmān b. ʿAwf.md` are **featured master entries**, built far
longer than the rest. Badr was rewritten from its pages in Nov 2026 and is footnoted throughout;
`ʿAbd al-Raḥmān b. ʿAwf` is the reference for *depth and structure only* — not for sourcing (it still
carries uncited and other-work material; run `python3 audit.py --note "ʿAbd al-Raḥmān b. ʿAwf"`).
Match a note's depth to its counterparts, not to these, unless the user asks for a master entry.

**Unresolved links are intentional.** Links are written eagerly so the graph connects when a note is
created; ~83 targets currently have no note. **Do not "fix" unresolved links by removing them.** When
creating a note for one, give it the full frontmatter and body skeleton for its type, and add it to the hub.

## Verification status — `unverified` / `verified` (human-only)

Every note carries the tag `unverified`. It records whether **the user has personally checked the note
against the books**. Only the user changes it.

- Never add `verified`, never remove `unverified`, never infer verification from a clean audit run.
- New notes get `unverified`.
- If you make a substantive change to a note the user has marked `verified`, leave the tag alone and
  tell the user which notes you changed, so they can re-check them.

## Sourcing rules (absolute)

The vault relies exclusively upon **five canonical sources**, each with a defined role:

| # | Source | Role | Cited by | File |
| --- | --- | --- | --- | --- |
| 1 | ***Ṣaḥīḥ al-Bukhārī*** (d. 256 AH), al-Sulṭāniyyah edition | Highest authority for any report it contains | ḥadīth number | `sources/1681.epub` |
| 2 | ***Ṣaḥīḥ Muslim*** (d. 261 AH), ed. Muḥammad Fuʾād ʿAbd al-Bāqī | Highest authority for any report it contains | ḥadīth number (the bracketed one) | `sources/1727.epub` |
| 3 | ***Subul al-Hudā war-Rashād fī Sīrat Khayr al-ʿIbād***, Imām al-Ṣāliḥī (d. 942 AH). Dār al-Kutub al-ʿIlmiyyah, Beirut, 1414/1993, 12 vols | The narrative, campaign and geographical backbone | vol:page | `sources/1693.epub` |
| 4 | ***al-Iṣābah fī Tamyīz al-Ṣaḥābah***, al-Ḥāfiẓ Ibn Ḥajar (d. 852 AH). Dār al-Kutub al-ʿIlmiyyah, Beirut, 1415/1995, 8 vols, ed. ʿĀdil ʿAbd al-Mawjūd & ʿAlī Muʿawwaḍ | Biographies of the Ṣaḥābah | vol:page (and entry no.) | `sources/9767.epub` |
| 5 | ***al-Bidāyah wa-l-Nihāyah***, Ibn Kathīr (d. 774 AH), ed. ʿAbdullāh b. ʿAbd al-Muḥsin al-Turkī. Dār Hajr, 1417–1419/1997–98, 21 vols | **Only** for what follows the Prophet's ﷺ death — vol. 8, p. 79 onward | vol:page | `sources/4445.epub` |

**Precedence.** Where sources differ, the Ṣaḥīḥayn lead: give their wording and present the other report
as a variant ("in another report…"). Between *Subul al-Hudā* and *al-Iṣābah*, follow the subject — *Subul*
for events, *al-Iṣābah* for a Companion's name, lineage and dates — and report a real disagreement as one.
*al-Bidāyah* is used only where the first four are silent, and only for the period after the Prophet's ﷺ
death; `audit.py` flags any *al-Bidāyah* citation to a page before 8:79.

**Scope — the prophetic era comes first.** The current priority is the Prophet's ﷺ life and the Ṣaḥābah
within it. Do not create new notes on the period after his death, and do not expand the existing ones,
unless the user asks for it. When such a note is rewritten, it is rewritten from these sources and may be
short.

This is a religious text: **every statement in every note must trace to one of these five books and be
verifiable on the page or ḥadīth cited.** This rule overrides helpfulness, completeness and fluency — an incomplete
note that is fully sourced is correct; a rich note carrying unsourced background is defective, however
accurate that background may be.

**Do not add anything from general knowledge of the sīrah**, however well established. If none of the
books mentions a detail, it does not enter the vault. Where a fact is needed but absent, say so
explicitly ("the sources do not give his death date").

**Read before writing.** A heading, a chapter title or an index entry establishes only *where* a topic is
treated, never the content of a claim. Before writing or editing a claim, read the page and write from
its text:

```bash
python3 audit.py --page S 6:77-78      # Subul al-Hudā, vol. 6, pp. 77–78 (matn, then taḥqīq)
python3 audit.py --page I 7:99-100     # al-Iṣābah, vol. 7, pp. 99–100
python3 audit.py --page B 9:414        # al-Bidāyah, vol. 9, p. 414
python3 audit.py --page K 3039         # Ṣaḥīḥ al-Bukhārī, ḥadīth 3039 (the page(s) it is on)
python3 audit.py --page M 1779         # Ṣaḥīḥ Muslim, ḥadīth 1779
```

For the Ṣaḥīḥayn, find the report from the citation *Subul al-Hudā* gives ("rawāhu al-Bukhārī…") or by
searching the EPUB text, then confirm its number with `--page` before citing it.

Never cite a page whose text you have not inspected, and read the **whole** page (see failure modes).

### What may and may not carry a citation

- **Only what the page says.** A citation certifies the whole claim before it. Do not attach a citation
  to framing, context or inference the page does not contain ("following the Khandaq…", "to neutralise
  the confederates of Quraysh…"). If the context is needed and is sourced elsewhere, cite that page; if
  not, leave it out.
- **No editorial analysis presented as sourced.** Sections such as "Strategic Significance", "Lessons" or
  "Legacy" are acceptable only where they report what al-Ṣāliḥī or Ibn Ḥajar themselves say (e.g. the
  *tanbīhāt* and *fawāʾid* in *Subul*). Otherwise omit them.
- **Keep the source's qualifiers — never upgrade them.** A report introduced with *qīla*, *ruwiya*,
  *zuʿima*, *yuqālu* stays "it is said / it is reported". A *khilāf* (two counts, two dates, two names)
  is given as a *khilāf*. The author's own verdict — *al-ṣaḥīḥ*, *al-ashhar*, *laysa bi-shayʾ*, a grading
  he quotes — is reported as his verdict. Example: *al-Iṣābah* 7:100 says *wa-qīla innahu mimman shāraka
  fī qatl Musaylimah*; writing "he struck Musaylimah down" turns a weak report into a fact.
- **Nasab exactly as the book gives it.** Do not extend a lineage beyond what the cited entry states.
- **Other works appear only through the five books.** When al-Ṣāliḥī, Ibn Ḥajar or Ibn Kathīr quotes
  Ibn Isḥāq, al-Wāqidī, Ibn Saʿd, al-Ṭabarī, al-Ṭabarānī, Aḥmad etc., you may name that authority, framed
  as transmitted and cited to the canonical page — `(al-Ṭabarānī, as cited in *Subul al-Hudā*, 4:192)` or
  "al-Ṣāliḥī reports from Ibn Isḥāq that … (*Subul al-Hudā*, 4:192)". Never cite another work's own
  pagination or ḥadīth number, and never list another work in a note's References. (al-Bukhārī and Muslim
  are now sources in their own right: cite them directly by number.) `audit.py` flags other works cited without
  `as cited in` / `apud` / `quoted by` framing.
- **Arabic quotations are verbatim** from the cited page (vocalisation may be added). If you are
  paraphrasing, do not use «…».

### The two tiers, and how to cite them

*Subul al-Hudā* and *al-Iṣābah*, in these editions, each contain two voices (the same holds for
al-Turkī's apparatus to *al-Bidāyah* and ʿAbd al-Bāqī's notes to Muslim). **Both may be cited; they must be told apart.**

| Source & tier | Whose words | Cite as |
| --- | --- | --- |
| *Subul al-Hudā*: matn | Imām al-Ṣāliḥī (d. 942 AH) | `*Subul al-Hudā*, 4:50` |
| *Subul al-Hudā*: taḥqīq | Editors (1414/1993), citing al-Khulāṣah, al-Taqrīb, al-Iṣābah, al-Aʿlām… | `*Subul al-Hudā*, 1:68 n. 5 (taḥqīq)` |
| *al-Iṣābah*: matn | al-Ḥāfiẓ Ibn Ḥajar (d. 852 AH) | `*al-Iṣābah*, 4:145` or `*al-Iṣābah*, no. 4835 (4:145)` |
| *al-Iṣābah*: taḥqīq | Editors (1415/1995), apparatus | `*al-Iṣābah*, 4:145 n. 1 (taḥqīq)` |

In the EPUBs the apparatus is every `<p class="hamesh">` on a page; everything else is matn
(`--page` prints them separately). The apparatus is where transmitters' biographies (death years, gradings,
work titles) live; it is never to be presented as the author's own statement.

### Citation format

- **Footnotes** (new and rewritten notes): put `[^key]` after the sentence or clause it supports, and the
  definitions at the end of the note — `[^s4.192]: *Subul al-Hudā*, 4:192–193.` Keys are `s<vol>.<page>`,
  `i<vol>.<page>` or `b<vol>.<page>`, and `bukh<no.>` / `musl<no.>` for the Ṣaḥīḥayn —
  `[^bukh3039]: *Ṣaḥīḥ al-Bukhārī*, no. 3039.` (add a letter for a second footnote on the same page: `i3.146b`); reuse a key for a
  repeated citation. A definition may add a short note after the citation (which report the wording comes
  from, a variant name), and the definition must cite the page for that note too. `audit.py` expands each
  footnote into its claim before checking it.
- Older notes cite inline after each claim — `(*Subul al-Hudā*, 4:192–193)`, `(*al-Iṣābah*, 1:533; 3:461)`
  — which remains valid; convert to footnotes when a note is rewritten.
- `primary_source:` in frontmatter gives the source(s), volume(s) and page range(s).
- The bare shorthand `(vol. N, pp. X–Y)` **always means *Subul al-Hudā***. *al-Iṣābah* pagination must
  always name the book (`*al-Iṣābah*, vol. 3, pp. 460–461, no. 4365`) or it is read — and validated — as
  Subul.
- Longer notes end with a numbered `## References` list in full bibliographic form, **containing only the
  canonical books the note actually cites**.
- Never invent a volume/page. If you cannot find the page, say so rather than fabricating one.

### Gregorian dates — exempt

The books date in Hijrī. **Hijrī→Gregorian conversion is outside the scope of the sourcing rule** — it is
checkable arithmetic, not a claim about the sīrah — so `CE` dates may be given. This is the single
exemption. Ages, troop counts, casualty figures, distances and Hijrī dates are content and fully governed.

### Failure modes seen in this vault

- **Close but wrong.** `4:49` for a martyrdom at `4:45` passes every mechanical check. The Badr audit
  found fourteen of these in one entry. `audit.py` reports "found at V:P" when a missing item is on a
  neighbouring page — treat that as a probable mis-citation and read both pages.
- **A passing mention cited for a narrative.** *Subul al-Hudā* 11:275 is about ʿUmar's death and names
  al-Yarmūk once, in a list of conquests; it was cited for a full account of the battle (Heraclius's
  farewell, al-Wāqūṣah, chained soldiers) that is on no cited page.
- **General knowledge with a nearby citation attached.** Typical signs: long nasab chains, named
  sub-battles or places, dramatic detail ("dozens of wounds"), campaign lists ("Khaybar and Ḥunayn") that
  the cited entry does not mention.
- **Reading the top of a page is not reading the page.** A page often opens with the tail of the previous
  section's glossary. `6:94` opens with a lexical *tanbīh* on weights and zakāt and then carries the whole
  Dūmat al-Jandal expedition. Judging it by its first lines produced a wrong "correction" that had to be
  reverted.
- **A corrected claim can survive elsewhere.** "Christian Arab confederation of Banū Kalb" was removed
  from `Banū Kalb` but still stood in `ʿAbd al-Raḥmān b. ʿAwf`. After fixing a claim, grep the vault.

### Where the books are silent

Some authorities *Subul al-Hudā* cites have no biographical entry in *Subul* or *al-Iṣābah* (e.g. Mūsā
b. ʿUqbah, Ibn Kathīr, al-Ṣāliḥī himself). Their notes record only what is attested — that a book cites
them, which works it names, the verdicts it takes from them — and say plainly that the sources supply no
biography. (*al-Bidāyah*'s obituaries may cover some of them, but they belong to the post-prophetic period
and wait until that work is taken up.) For the period after the Prophet's ﷺ death, use *al-Bidāyah* where
the other four are silent; a note may still be short, or say what is not recorded, rather than be filled
from elsewhere.

### Biographical enrichment for Ṣaḥābah

When creating or updating a Ṣaḥābī's note, read their *al-Iṣābah* entry (and any *Subul al-Hudā*
treatment) in full, and record **what those entries give**: lineage to common progenitors, maternal
lineage, tribe and clan, *ḥilf* and *walāʾ*, marriages, *riḍāʿah*, progeny, order of conversion, trials in
Makkah, the hijrahs, campaigns, death date, age, place and burial. Where an entry is silent on one of
these, the note is silent or says so — the list is what to look for, not what must be filled.

## Note conventions

**Frontmatter.** Every note carries `title`, `arabic` (Arabic-script name), `type`, `tags`, and almost
always `aliases` and `primary_source`. Other keys are deliberately **type- and note-specific**
(`date_hijri`, `location`, `commanders_muslim` / `commanders_enemy`, `strength_muslim`, `casualties_enemy`,
`quranic_reference(s)`, `birth` / `death`, `surah_number` / `total_ayahs`…) — do not normalise them into a
fixed schema. Frontmatter values are claims too: a number in `strength_muslim` needs the same source as
one in the body. A value containing a wikilink must be quoted (`location: "[[Badr]]"`); multi-valued keys
are YAML lists.

**Transliteration is strict IJMES** (`ʿAlī b. Abī Ṭālib`, `Ghazwat Uḥud`, `Ṣulḥ al-Ḥudaybiyah`) and is
load-bearing: file names, wikilinks and aliases use the same diacritics, so a mistyped `ʿ`/`ʾ` or a
missing macron silently breaks a link. Copy names from existing notes rather than retyping them. One
inconsistency is preserved deliberately: the Prophet's note is `Muḥammad b. ʻAbdullah.md` (curly `ʻ`, no
diacritics on Abdullah), so it is always linked with a display alias —
`[[Muḥammad b. ʻAbdullah|Muḥammad b. ʿAbdullāh]] ﷺ`.

**Writing style — encyclopedic prose.** Write for an educated general reader, in the manner of a good
Wikipedia article; `Abū Dujānah.md` is the model.
- `# Title (Arabic script)`, an italic epithet line, then a **lead paragraph** summarising the subject
  (sourced like everything else), then plain-titled `##` sections (Name, Early life, Badr, Uḥud, Later
  campaigns, Death…), in chronological order.
- **Paragraphs, not bullet lists.** Tell the story in connected sentences. Lists and tables only for
  material that really is a list — rosters, participants, *asbāb al-nuzūl*.
- **Name people as participants, not as sources.** "al-Zubayr followed him to see what he would do", not
  "al-Ṣāliḥī reports from Isḥāq b. Rāhawayh and al-Bazzār from al-Zubayr that…". The footnote carries the
  attribution. Name an authority in the text only when the reader needs it: a weak report ("according to
  one report", "it is said"), a disagreement ("others credit Thābit b. al-Jidhʿ"), or a verdict ("the
  better-known view is…"). This changes the wording, never the rule: a *qīla* is still marked as one.
- **Arabic sparingly**: quote in `«…»` (blockquote, English beneath) for famous or decisive words; otherwise
  paraphrase in English. Vocalisation notes, chains of transmission and editors' remarks go in footnotes.
- `> [!NOTE]` callouts only for genuine asides a general reader may skip.

**Honorifics** are Unicode ligatures written bare after the name, as the source text does. Gender and
number must agree, so this is never a blind find-and-replace:

| Char | Codepoint | Reading | Use for |
| --- | --- | --- | --- |
| ﷺ | U+FDFA | ṣallā Allāhu ʿalayhi wa-sallam | the Prophet ﷺ |
| ﵁ | U+FD41 | raḍiya Allāhu ʿanhu | one male Companion |
| ﵂ | U+FD42 | raḍiya Allāhu ʿanhā | one female Companion |
| ﵃ | U+FD43 | raḍiya Allāhu ʿanhum | a group of men |
| ﵄ | U+FD44 | raḍiya Allāhu ʿanhumā | two people |
| ﵅ | U+FD45 | raḍiya Allāhu ʿanhunna | a group of women |
| ﵊ | U+FD4A | ʿalayhi al-salām | prophets and angels |
| ☠ | — | — | antagonists who died in opposition |

**Tags** repeat `type` first, then era (`makkan_era`), Hijrī year (`2-ah`), role (`sahabi`, `badri`,
`ashara_mubashsharah`, `ansari`, `muhajir`, `munafiq`), topic, and the verification tag above. Reuse the
existing vocabulary.

## Audit tooling (`audit.py`)

```bash
python3 audit.py                          # structure + content-triage summary (≈7 s)
python3 audit.py --note "Sariyyat al-Ghamr" # every finding for one note
python3 audit.py --sheet "Sariyyat al-Ghamr" # review/<note>.sheet.md: claims, flags, full cited pages
python3 audit.py --report review/_triage.md  # every finding for every note, as Markdown
python3 audit.py --page S 6:77-78          # print pages (S = Subul al-Hudā, I = al-Iṣābah)
python3 audit.py --links | --citations | --no-content | --reindex
```

**Structural checks** — the exit code is non-zero if any fails:
1. *Citation bounds*: every cited vol:page (every page of a list or range) and every cited ḥadīth number
   exists in its EPUB.
2. *Hub completeness*: every note is linked from `The Sīrah.md`.
3. *Wrapped links*: no wikilink contains a line break.
4. *Frontmatter*: required fields present.
Unresolved wikilinks are counted but are not failures (they are intentional).

**Content triage** — informational. Each line is split at its citations; the text before a citation is
checked against the Arabic of the pages it cites (citations spanning more than 12 pages are skipped):

| Flag | Meaning |
| --- | --- |
| `number` | a numeral in the claim matches no digit or Arabic number word (incl. compounds) on the pages |
| `term` | a transliterated name's consonantal skeleton is absent from the pages |
| `phrase` | an italic transliterated Arabic phrase is absent from the pages |
| `quote` | a «…» quotation is not on the pages (shows % of its words found) |
| `apparatus` | a term occurs only in the editors' footnotes but is cited as matn |
| `uncited` | a substantive line with no citation to any of the five books |
| `other-work` | another work cited directly, or listed in References |
| `scope` | *al-Bidāyah* cited for the period before the Prophet's ﷺ death (before vol. 8, p. 79) |

"found at V:P" means the missing item does appear within three pages of the citation.

**What a flag means, and what it does not.** The triage is a list of places to look, not a verdict. A
flag may be sound (an English exonym, a spelling variant, an orthographic alif, a Qurʾān quotation in
different script). An *unflagged* claim is **not** thereby verified: the checks see numbers, names and
quotations, not meaning — "fought valiantly", a reversed relationship, a wrong attribution or a *qīla*
turned into a fact all pass silently. Only reading the page verifies a claim.

**Workflow.** After writing or editing a note: run `--note` on it and resolve every flag — correct the
claim, correct the citation, or (if the flag is a false positive) leave it with a reason you can state.
Then run the plain audit to confirm no structural failures. For the user's own verification, generate a
`--sheet`.
