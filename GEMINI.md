# GEMINI.md

This file provides guidance to Antigravity when working with code in this repository.

## What this repository is

This is **not a software project**. It is an Obsidian vault, git-backed, containing an English-language
scholarly wiki of the *Sīrah* (Prophetic biography) written from an orthodox Sunni perspective. There is
no build, no tests, no lint, no dependencies. The deliverable is the Markdown notes themselves and the
link graph between them.

All 80 notes live **flat in the repository root** — no folders. `.obsidian/` (config + the `obsidian-git`
plugin) is committed alongside them.

## Git workflow

Commits are made automatically by the Obsidian **obsidian-git** plugin, not by hand:
- Commit message template: `vault backup: {{date}}` with format `YYYY-MM-DD HH:mm:ss`
- Sync method is `merge`, `pullBeforePush` is on, auto-intervals are all disabled (commit is manual-trigger from inside Obsidian)

Expect `.obsidian/workspace.json` and `.obsidian/graph.json` to show up as noise in most diffs. When
committing from the CLI, follow the existing `vault backup: <timestamp>` convention so history stays uniform.

## Architecture of the knowledge graph

[The Sīrah.md](The%20Sīrah.md) is the hub (`type: index`) and the only navigational entry point. It holds the
canonical chronological master index of events (Makkan era → early Madinan → major *ghazawāt* → culmination),
plus registers for biographies, Qurʾānic nodes, and geography. **Any new note must be added to the matching
section of this hub**, or it becomes an orphan — there is no folder structure to discover it by.

Notes are typed via frontmatter `type:`, and each type has its own frontmatter shape and body skeleton
(counts below drift as notes are added; `type` is the stable part):

| `type` | Count | Body pattern |
| --- | --- | --- |
| `event` | 35 | Numbered `## 1. Strategic Context`, deployment, reversal/climax, aftermath |
| `person` | 29 | `## 1. Lineage/Before Islam`, `## 2. Key Sīrah Milestones`, death & burial |
| `place` | 8 | Topography & significance, linked to its `primary_event` |
| `text` | 6 | Qurʾān sūrahs: overview, then an *asbāb al-nuzūl* table (ayah / Arabic excerpt / occasion / persons) |
| `group` | 7 | Tribes and clans: lineage, territory, role in the Sīrah, principal members |
| `source` | 1 | [Subul al-Hudā war-Rashād.md](Subul%20al-Hudā%20war-Rashād.md) — the vault's citation backbone |
| `index` | 1 | The hub |

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

## Sourcing rule (absolute)

**Subul al-Hudā war-Rashād is the ONLY permitted source of content.** This is a religious text; every
statement in every note must trace back to it and be verifiable there. This rule overrides
helpfulness, completeness, and fluency — an incomplete note that is fully sourced is correct, and a
rich note carrying unsourced background is defective, however accurate that background may be.

**Do not add anything from general knowledge of the sīrah**, however well established: no dates,
places, genealogies, kunyas, death years, work titles, appraisals, hadith numbers, or narrative
detail that is not in the book. If the book does not say it, it does not go in the vault. Where a
fact is genuinely needed and absent, say it is absent rather than supplying it.

**Working method — read before writing.** A heading title or an index entry establishes only *where a
topic is treated*, never the content of a claim. Before writing a sentence, read the page it will
cite in `~/Documents/repos/sirah-corpus/corpus.jsonl` and write from that text. Never cite a page
whose body you have not read.

### The two tiers, and how to cite them

The vault cites the Dār al-Kutub al-ʿIlmiyyah edition (Beirut, 1414/1993), which contains two
distinct authorial voices. **Both are permitted; they must be told apart**, because they do not carry
equal weight:

| Tier | Whose words | Cite as |
| --- | --- | --- |
| **Matn** — al-Ṣāliḥī's own text | Imām al-Ṣāliḥī (d. 942 AH) | `*Subul al-Hudā*, 4:50` |
| **Taḥqīq** — the editors' critical apparatus | ʿĀdil ʿAbd al-Mawjūd & ʿAlī Muʿawwaḍ (1414/1993), themselves citing al-Khulāṣah, al-Taqrīb, al-Iṣābah, al-Aʿlām | `*Subul al-Hudā*, 1:68 n. 5 (taḥqīq)` |

The apparatus is where the *transmitters' biographies* live — death years, gradings, work titles. It
is the only place in the book such material exists, so notes on the authorities depend on it
entirely. It is never to be presented as al-Ṣāliḥī's own statement.

The corpus separates the tiers mechanically: each page's `body` is matn, its `footnotes` array is
taḥqīq.

### Auditing what is already written

`~/Documents/repos/sirah-corpus/audit.py` cross-checks every numeral asserted in a note against the
numerals actually present on the pages that note cites (Arabic-Indic digits and number-words, matn
plus apparatus). It produces a triage list, not a verdict — a flagged number may still be sound, and
an unflagged one is not thereby verified. Run it after any batch of writing:

```bash
cd ~/Documents/repos/sirah-corpus && python3 audit.py
```

Known false positives: Qurʾānic sūrah and āyah numbers, Hijrī years the book writes as word-compounds
(`مات سنة إحدى وخمسين ومائة` = 151), and Gregorian years — see below.

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

### Where the book is silent

Some authorities the book cites are given no biographical entry in it — as of this audit,
**Ibn Ḥajar al-ʿAsqalānī, Mūsā b. ʿUqbah, Ibn Kathīr and al-Ṣāliḥī himself** have none. Their notes
must therefore record only what the book does attest — that it cites them, which of their works it
names, and the verdicts it takes from them — and must say plainly that the book supplies no
biography. Do not fill the gap from elsewhere.

**Citations.** Every substantive claim is anchored to `*Subul al-Hudā*, <vol>:<page>` inline, with `primary_source`
in frontmatter giving the volume and page range. The bare `(vol. N, pp. X–Y)` shorthand **always means Subul
al-Hudā** — any other work's pagination must name that work explicitly (`*al-Ṭabaqāt al-Kubrā* 3:522–525`), or it
reads as a Subul citation and will fail validation against the volume bounds. Longer notes close with a numbered `## References` list in full
bibliographic form (al-Ṣāliḥī, Ibn Hishām, Ibn Kathīr, al-Bukhārī, Muslim…). Never invent a volume/page number —
if the citation isn't known, say so rather than fabricating one.

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
the vocabulary is already established across the vault.

## Intentional stubs and unresolved links

Roughly 118 of the ~198 distinct wikilink targets have no note yet (classical authorities like `[[Ibn Kathīr]]`,
`[[Ibn Isḥāq]]`; tribes like `[[Banū Hāshim]]`; secondary companions; sub-events like `[[Bayʿat al-Riḍwān]]`).
This is by design — links are written eagerly so the graph is ready when a note is created. **Do not "fix"
unresolved links by removing them.** `Ibn Ḥajar al-ʿAsqalānī.md` exists but is empty (0 bytes), a placeholder
awaiting content.

When creating one of these stubs, give it the full frontmatter + body skeleton for its `type`, and add it to
the correct section of the hub.

## Importing other agent configs

`~/.codex/config.toml` and `~/.gemini/settings.json` are both present on this machine. If you'd like their
MCP servers, slash commands, subagents, skills, or instructions brought into Claude Code, reply `/import` to
scan and list what's importable, then `/import --yes=<digest>` (the scan output names the digest) to apply the
user-level items. If `/import` isn't available on this surface, run `claude import` from a terminal instead.
