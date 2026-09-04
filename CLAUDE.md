# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
