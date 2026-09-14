# GEMINI.md

This file provides guidance to Antigravity when working with code in this repository.

## What this repository is

This repository is an Obsidian vault, git-backed, containing an English-language scholarly wiki of the *Sīrah* (Prophetic biography) written from an orthodox Sunni perspective. While authoring occurs directly in Markdown inside Obsidian, the repository also functions as the static source for **nabiwiki**, built with **Quartz v4** and published live to **https://nabiwiki.netlify.app/**.

The knowledge graph has expanded to **over 470+ articles (approaching 500+ across all registers)**. All article notes live **flat in the repository root** — no folders. Configuration directories (`.obsidian/`, `.github/`) and Quartz build infrastructure (`build.sh`, `quartz.config.yaml`, `patch-quartz.mjs`, `custom.scss`, `netlify.toml`) live alongside them.

## Git workflow and CI/CD deployment

### Git commits
Commits are managed primarily by the Obsidian **obsidian-git** plugin:
- Commit message template: `vault backup: {{date}}` with format `YYYY-MM-DD HH:mm:ss`
- Sync method is `merge`, `pullBeforePush` is on, auto-intervals are disabled (commits are triggered manually from inside Obsidian or when synchronizing).
- When committing from the CLI, follow the existing `vault backup: <timestamp>` convention so git history stays uniform.

### Static build & CI/CD deployment
Pushing to the `main` branch on GitHub automatically triggers a deployment workflow (`.github/workflows/deploy.yml`):
- **Engine**: Jacky Zhao's Quartz v4 (`build.sh` clones Quartz to `.quartz/` if absent, installs dependencies with Node 22).
- **Customizations**:
  - `quartz.config.yaml`: Sets page title (`nabiwiki (السيرة)`), disables SPA mode, configures Noto Serif typography and dark/light themes, and filters non-content files (`ignorePatterns`).
  - `custom.scss`: Enforces Noto Serif for English and Noto Naskh Arabic for Arabic script, styling blockquotes with classical typography.
  - `patch-quartz.mjs`: Critical ASCII slug fold patch. Normalizes complex IJMES diacritics (`ʿ`, `ʻ`, `ʾ`, `ā`, `ī`, `ū`, `ḍ`, `ṣ`, etc.) and Arabic script into clean lowercase ASCII URL slugs, preventing infinite redirect loops and 404 errors on CDN hosting.
  - `build.sh`: Generates static HTML into `public/`, then copies `the-sirah.html` to `index.html` so the canonical hub serves as the website's homepage.
- **Hosting**: Deployed directly to Netlify via `netlify-cli` at **https://nabiwiki.netlify.app/**.

## Architecture of the knowledge graph

[The Sīrah.md](The%20Sīrah.md) is the hub (`type: index`) and the only navigational entry point. It holds the
canonical chronological master index of events (Makkan era → early Madinan → major *ghazawāt* → culmination),
plus registers for biographies, Qurʾānic nodes, and geography. **Any new note must be added to the matching
section of this hub**, or it becomes an orphan — there is no folder structure to discover it by.

Notes are typed via frontmatter `type:`, and each type has its own frontmatter shape and body skeleton:

| `type` | Approx. Count | Body pattern |
| --- | --- | --- |
| `person` | 267+ | `## 1. Lineage & Background`, `## 2. Key Sīrah Milestones`, `## 3. Merits & Character`, death & burial |
| `event` | 106+ | Numbered `## 1. Strategic Context`, deployment, battle/crisis climax, aftermath & Qurʾānic commentary |
| `group` | 39+ | Lineage (*nasab*), territory, alliances (*ḥilf*), role in the Sīrah, notable figures |
| `place` | 36+ | Topography, prophetic milestones, primary events, coordinates/region |
| `text` | 20+ | Qurʾān sūrahs: revelation context, thematic overview, *asbāb al-nuzūl* table (ayah / Arabic text / occasion / persons) |
| `source` | 2 | Primary canonical source descriptions ([Subul al-Hudā war-Rashād.md](Subul%20al-Hudā%20war-Rashād.md) and [al-Iṣābah fī Tamyīz al-Ṣaḥābah.md](al-Iṣābah%20fī%20Tamyīz%20al-Ṣaḥābah.md)) |
| `index` | 1 | The hub: [The Sīrah.md](The%20Sīrah.md) |

Two notes are deliberately built out as **featured master entries** far longer than the rest and are the
reference for maximal depth: [Ghazwat Badr al-Kubrā.md](Ghazwat%20Badr%20al-Kubrā.md) (17 numbered sections,
~550 lines, ending in a participants table and a numbered classical-citation list) and
[ʿAbd al-Raḥmān b. ʿAwf.md](ʿAbd%20al-Raḥmān%20b.%20ʿAwf.md). Match a note's depth to its counterparts, not
to these, unless the user asks for a master entry.

## Note conventions

**Frontmatter.** Every note carries `title`, `arabic` (Arabic script name), `type`, `tags`, and almost always
`aliases` and `primary_source`. Beyond that, keys are intentionally **type- and note-specific** — `date_hijri`,
`location`, `commanders_muslim` / `commanders_enemy`, `strength_muslim`, `casualties_enemy`,
`quranic_reference(s)`, `birth` / `death`, `surah_number` / `total_ayahs`. Do not try to normalise these into a
fixed schema; add the keys the individual subject actually warrants. Any frontmatter value containing a
wikilink must be quoted (`location: "[[Badr]]"`), and multi-valued ones become YAML lists.

**Transliteration is strict IJMES** (`ʿAlī b. Abī Ṭālib`, `Ghazwat Uḥud`, `Ṣulḥ al-Ḥudaybiyah`) and is load-bearing:
file names, wikilinks, and aliases all use the same diacritics, so a mistyped `ʿ`/`ʾ` or missing macron silently
breaks the link graph. Copy names from existing notes rather than retyping them. Note the one inconsistency to
preserve as-is: the Prophet's note is filed as `Muḥammad b. ʻAbdullah.md` (curly `ʻ`, undiacriticised `Abdullah`)
and is therefore always linked with a display alias — `[[Muḥammad b. ʻAbdullah|Muḥammad b. ʿAbdullāh]] ﷺ`.

## Sourcing rules (absolute)

The vault relies exclusively upon **two canonical primary sources**:
1. **Subul al-Hudā war-Rashād** by Imām Muḥammad b. Yūsuf al-Ṣāliḥī (d. 942 AH) — the primary narrative, geographical, and campaign backbone (Dār al-Kutub al-ʿIlmiyyah, Beirut, 1414/1993, 12 vols).
2. **al-Iṣābah fī Tamyīz al-Ṣaḥābah** by al-Ḥāfiẓ Ibn Ḥajar al-ʿAsqalānī (d. 852 AH) — the premier biographical encyclopedia for the Ṣaḥābah (Dār al-Kutub al-ʿIlmiyyah, Beirut, 1415/1995, 8 vols, ed. ʿĀdil ʿAbd al-Mawjūd & ʿAlī Muʿawwaḍ).

This is a religious text; every statement in every note must trace back to one of these two sources and be verifiable there. This rule overrides helpfulness, completeness, and fluency — an incomplete note that is fully sourced is correct, and a rich note carrying unsourced background is defective, however accurate that background may be.

**Biographical Enrichment Protocol for Ṣaḥābah**:
Whenever a Ṣaḥābī's note is created or updated, consult their entry in both *Subul al-Hudā* and *al-Iṣābah* (`sources/9767.epub`). Flesh out their profile comprehensively, with particular emphasis on:
- Detailed genealogical chains tracing ancestors back to common tribal progenitors (linking them to other Companions and to the Prophet ﷺ).
- Maternal lineage, tribal and clan affiliations (*al-qabāʾil wal-buṭūn*), confederacies (*ḥilf*), and clientship (*walāʾ*).
- Kinship networks, marriages, fosterage (*riḍāʿah*), and progeny.
- Sequence of conversion, early trials in Makkah, participation in the migrations, and roles across all military campaigns.
- Precise death dates, ages, locations, and burial sites.

**Do not add anything from general knowledge of the sīrah**, however well established. If neither book mentions a detail, it does not enter the vault. Where a fact is needed but absent from both, state its absence explicitly.

### Repository source corpus locations & structure

The authoritative Arabic corpora are stored directly within the repository under `sources/` and tracked in git:
- **Subul al-Hudā war-Rashād**: `sources/1693.epub` (12 volumes, 5,750+ page files)
- **al-Iṣābah fī Tamyīz al-Ṣaḥābah**: `sources/9767.epub` (8 volumes, 4,400+ page files)

Having the EPUBs tracked directly in git ensures that collaborators immediately have the full primary source corpus upon cloning, without requiring manual downloads or external corpus configuration. Both files are ignored by Quartz during static builds via `ignorePatterns` in `quartz.config.yaml`.

**Internal page structure**:
Both EPUBs follow standard Shamela formatting within `OEBPS/text/`:
- **Matn**: Primary text is contained in regular `<p>` tags (and section headers in `<h3>`, `<h4>`, `<h5>`).
- **Taḥqīq / Footnotes**: The apparatus is encapsulated in `<p class="hamesh">...</p>`.
- **Pagination markers**: Every page ends with a centered volume and page indicator:
  `<p class="text-center">الجزء: X - الصفحة: Y</p>`
- This enables instant programmatic verification via `audit.py` using Python's standard `zipfile` library.

**Working method — read before writing.** Before writing or updating a claim, inspect the actual text in `sources/1693.epub` or `sources/9767.epub`. Never cite a volume or page without verifying that the source text contains the asserted facts.

### The two tiers, and how to cite them

The vault cites the Dār al-Kutub al-ʿIlmiyyah editions of both works, each containing two distinct authorial voices that must be told apart:

| Source & Tier | Whose words | Cite as |
| --- | --- | --- |
| **Subul al-Hudā: Matn** | Imām al-Ṣāliḥī (d. 942 AH) | `*Subul al-Hudā*, 4:50` |
| **Subul al-Hudā: Taḥqīq** | Editors (1414/1993), citing al-Taqrīb, al-Khulāṣah, al-Aʿlām, etc. | `*Subul al-Hudā*, 1:68 n. 5 (taḥqīq)` |
| **al-Iṣābah: Matn** | al-Ḥāfiẓ Ibn Ḥajar al-ʿAsqalānī (d. 852 AH) | `*al-Iṣābah*, 4:145` or `*al-Iṣābah*, no. 4835 (4:145)` |
| **al-Iṣābah: Taḥqīq** | Editors (1415/1995), apparatus | `*al-Iṣābah*, 4:145 n. 1 (taḥqīq)` |

The apparatus is where the *transmitters' biographies* live — death years, gradings, work titles. It is never to be presented as the primary author's own statement. In both EPUBs, each page's body is matn, while `<p class="hamesh">` contains taḥqīq.

### Gregorian dates — decided: exempt

The book is dated in Hijrī throughout; Gregorian equivalents appear only in the editors' Muqaddimah
(the Mawlid at *"20 April 571 CE"*, p. 6, and some AH/CE pairs at p. 37).

**Decision: Hijrī→Gregorian conversion is treated as outside the scope of the sourcing rule** — it is
checkable arithmetic, not a claim about the sīrah. Existing `CE` dates stay as they are, and new ones
may be given. This is the single stated exemption; it does not extend to anything else. Ages, troop
counts, casualty figures, distances and dates *within* the Hijrī calendar are content, and are
governed by the rule in full.

### Two failure modes the audit has actually hit

**A citation can be close but wrong, and nothing mechanical will catch it.** `4:49` for a martyrdom
that is at `4:45` passes every check — volume exists, page exists, resolves inside the volume bounds.
The Badr audit found fourteen of these in one entry. Only reading the page catches it.

**Reading the top of a page is not reading the page.** A page often carries the tail of the previous
section's glossary before its own narrative begins. `6:94` opens with a lexical *tanbīh* on weights
and zakāt and then, below it, carries the whole Dūmat al-Jandal expedition. Judging that page by its
first lines produced a wrong "correction" that had to be reverted. Read to the end of the page before
concluding a claim is unsupported.

Corollary: **a corrected claim can survive elsewhere in the graph.** The "Christian Arab
confederation of Banū Kalb" was removed from `Banū Kalb` and still stood in
`ʿAbd al-Raḥmān b. ʿAwf`. After fixing a claim, grep the vault for it.

### Where the primary texts are silent

Some authorities *Subul al-Hudā* cites are given no standalone biographical entry in it — such as **Mūsā b. ʿUqbah, Ibn Kathīr and al-Ṣāliḥī himself**. (Ibn Ḥajar al-ʿAsqalānī is the prominent exception: he is now a canonical primary source in his own right via *al-Iṣābah*, and his note ([Ibn Ḥajar al-ʿAsqalānī.md](Ibn%20Ḥajar%20al-ʿAsqalānī.md)) is fully authored). For authorities genuinely absent from both primary texts, the note must record only what the books attest — which works are cited and what narrations or gradings are transmitted — and must state plainly that the primary sources supply no biography. Do not fill the gap from unapproved external sources.

**Citations.** Every substantive claim is anchored to `*Subul al-Hudā*, <vol>:<page>` or `*al-Iṣābah*, <vol>:<page>` inline, with `primary_source` in frontmatter giving the source, volume, and page range. The bare `(vol. N, pp. X–Y)` shorthand **always means Subul al-Hudā** — any other work's pagination (including *al-Iṣābah*) must name that work explicitly (`*al-Iṣābah*, 4:145` or `*al-Ṭabaqāt al-Kubrā* 3:522–525`), or it reads as a Subul citation and will fail validation. Longer notes close with a numbered `## References` list in full bibliographic form (al-Ṣāliḥī, Ibn Ḥajar, Ibn Hishām, Ibn Kathīr, al-Bukhārī, Muslim…). Never invent a volume/page number — if the citation isn't known, say so rather than fabricating one.

**Body style.** `# Title (Arabic script)` followed by an italic epithet line; numbered `##` sections; Arabic
primary-text quotations in `«…»` guillemets inside blockquotes with an English rendering beneath; `> [!NOTE]`
callouts for provenance and scholarly asides.

**Honorifics use the Unicode ligatures, not ASCII abbreviations**, matching the typography of the source text
itself (Subul al-Hudā uses these throughout). They are written bare after the name — no parentheses — exactly
as ﷺ already is. **Gender and number must agree**, so this is never a blind find-and-replace:

| Char | Codepoint | Reading | Use for |
| --- | --- | --- | --- |
| ﷺ | U+FDFA | ṣallā Allāhu ʿalayhi wa-sallam | the Prophet ﷺ |
| ﵁ | U+FD41 | raḍiya Allāhu ʿanhu | one male Companion |
| ﵂ | U+FD42 | raḍiya Allāhu ʿanhā | one female Companion (Khadījah, ʿĀʾishah, Fāṭimah, Ṣafiyyah…) |
| ﵃ | U+FD43 | raḍiya Allāhu ʿanhum | a group of men (e.g. the Anṣār collectively) |
| ﵄ | U+FD44 | raḍiya Allāhu ʿanhumā | two people (a father and son, a pair of narrators) |
| ﵅ | U+FD45 | raḍiya Allāhu ʿanhunna | a group of women (the Mothers of the Believers) |
| ﵊ | U+FD4A | ʿalayhi al-salām | prophets and angels (Ibrāhīm ﵊, Jibrīl ﵊) |
| ☠ | — | — | antagonists who died in opposition |

All honorifics in the vault now use these ligatures; no ASCII forms (`(ra)`, `(as)`) remain.

**Tags** duplicate `type` as the first tag, then add era (`makkan_era`), Hijri year (`2-ah`), role
(`sahabi`, `badri`, `ashara_mubashsharah`, `ansari`, `muhajir`, `munafiq`), and topic. Reuse existing tags —
the vocabulary is already established across the vault. Notes also track editorial verification status: every note carries `unverified` by default, which is updated to `verified` upon manual review and primary-source verification.

## Intentional stubs and unresolved links

The vast majority of foundational stubs (such as `[[Ibn Isḥāq]]`, `[[Ibn Kathīr]]`, `[[Banū Hāshim]]`, `[[Bayʿat al-Riḍwān]]`, and `[[Ibn Ḥajar al-ʿAsqalānī]]`) have now been created into full articles. Currently, across 6,700+ wikilinks in the vault, only ~84 dangling targets remain, predominantly secondary biographical figures awaiting dedicated notes.

This link graph design is intentional — links are written eagerly so the web graph connects automatically when a note is authored. **Do not "fix" unresolved links by removing them.** When creating a new note to resolve one of these targets, give it the full frontmatter + body skeleton for its `type`, ensure strict adherence to IJMES transliteration, and add it to the matching section of [The Sīrah.md](The%20Sīrah.md).

## Automated Audit & Verification Tooling (`audit.py`)

The repository includes a dedicated verification script (`audit.py`) that audits the knowledge graph and verifies citations against the canonical EPUB corpora.

### Running the audit
```bash
python3 audit.py
```

### What it checks
1. **Canonical Citation Bounds**: Parses every citation to *Subul al-Hudā* and *al-Iṣābah* (over 9,900 citations vault-wide), verifying that volume and page numbers exist in `sources/1693.epub` and `sources/9767.epub`.
2. **Knowledge Graph Link Integrity**: Scans all 6,700+ wikilinks against all note titles and aliases, detecting broken links and generating fuzzy-match recommendations for near misses.
3. **Hub Completeness**: Enforces that 100% of all articles are indexed in [The Sīrah.md](The%20Sīrah.md) (detects orphans).
4. **Syntax & Wrap Errors**: Detects and flags multiline wikilinks (`[[\n...]]`) caused by markdown line wrapping.
5. **Frontmatter Integrity**: Enforces YAML schema fields (`title`, `arabic`, `type`, `tags`, `primary_source`).

### Useful CLI options
- `python3 audit.py`: Standard audit with summary statistics and failure details.
- `python3 audit.py --links`: Lists all unresolved wikilink targets with fuzzy match suggestions.
- `python3 audit.py --reindex`: Forces rebuilding the EPUB page cache (`sources/.index_cache.json`).

## Progress & Milestones

- **Corpus Ingestion**: The two primary source EPUBs (*Subul al-Hudā war-Rashād* 12 vols and *al-Iṣābah fī Tamyīz al-Ṣaḥābah* 8 vols) are integrated directly into the repository under `sources/` and tracked in git for seamless collaboration.
- **Audit Tooling Deployed**: `audit.py` created and operational. 100% of the 6,583 citations to *Subul al-Hudā* and 3,327 citations to *al-Iṣābah* are verified against primary EPUB text.
- **Hub & Link Graph Hardening**: 100% of content notes (471 articles) are linked in the hub with 0 orphans. All multiline link syntax errors eliminated. Missing aliases added across historical expeditions and tribal delegations.
- **Quartz & Netlify Pipeline**: `sources/` and `audit.py` added to `ignorePatterns`, ensuring clean static builds and CI/CD deploys to `https://nabiwiki.netlify.app/`.

## Importing other agent configs

`~/.codex/config.toml` and `~/.gemini/settings.json` are both present on this machine. If you'd like their
MCP servers, slash commands, subagents, skills, or instructions brought into Claude Code, reply `/import` to
scan and list what's importable, then `/import --yes=<digest>` (the scan output names the digest) to apply the
user-level items. If `/import` isn't available on this surface, run `claude import` from a terminal instead.
