---
name: rewrite-note
description: Rewrite a nabiwiki (Sīrah vault) note as footnoted encyclopedic prose, written from the claim ledgers in ledger/. Use when asked to rewrite, redo or convert a note in the obsidianbackup vault.
---

# Rewrite a nabiwiki note

Argument: the note's name, e.g. `Ghazwat al-Suwayq` (the file is `<name>.md` in the vault root).

`CLAUDE.md` holds the rules (five sources, precedence, scope, citation format, style, honorifics). Model
notes for the finished style: `Ghazwat al-Khandaq.md`, `Ghazwat Uḥud.md` (events), `Abū Dujānah.md` (people).

Rules that override everything here: **every sentence must rest on a ledger entry**; never touch the
`unverified`/`verified` tags; prophetic era first — do not expand post-prophetic notes unless the user asked.

## 1. Gather the ledgers

- Read the old note. Treat all of it as unverified leads.
- Find what is already read:
  ```bash
  grep -l "<name>" ledger/*.md                 # ledgers that feed or mention it
  grep -l "<Arabic name, unvocalised>" ledger/*.md
  ```
- **The note's own source must have a ledger.** For an event, its *Subul al-Hudā* chapter; for a Companion,
  their *al-Iṣābah* entry. If it has none, build it now by following `.claude/skills/ledger/SKILL.md`, then
  come back here.
- **Do not read other chapters for a person's note.** A Companion's Badr or Uḥud section is written from
  entries in ledgers that already exist. If the chapter has no ledger yet, the note says only what the
  *al-Iṣābah* entry says of it, and you list that chapter in your report as "not yet ledgered".
- Add this note to the `feeds:` line of every ledger you use.

## 2. Write from the entries

Read the ledgers, not the pages. Open a page (`python3 audit.py --page …`) only to settle something a
ledger leaves unclear — and then correct the ledger first.

- Each sentence states what one or more entries state, at the strength of their kind:
  `qīla` → "it is said / reported"; `khilāf` → both sides; `verdict` → as that person's verdict;
  `hedge` → the hedge kept; `via` → the footnote carries the attribution unless the reader needs it.
- A `- note:` in a ledger is the reader's remark, not the book's. It never becomes a claim: no "this most
  naturally means…", and no section listing what the source does not say. A silence is stated only where a
  reader would expect the fact (the year, a death date), in one clause.
- The italic epithet line, the lead and every frontmatter value are claims like any other: each clause
  needs its entry. ("Reached Buwāṭ without meeting the caravan" is not what «لم يلق كيدا» says.)
- A frontmatter value for a disputed point gives both sides or is left out; a reconciliation the page
  reports in the passive is not stated as fact.
- Names as the ledger has them; recurring phrases as `ledger/GLOSSARY.md` renders them.
- Nothing about the book's own arrangement ("al-Ṣāliḥī treats it after…") unless the reader needs it.
- Every `khilāf` and `verdict` entry about the subject appears in the note, usually in a disputes section.
- Footnotes are the entry's page: `S4.174.12` → `[^s4.174]`, `I7.99.03` → `[^i7.99]`, `K3039.01` →
  `[^bukh3039]`, `M1779.01` → `[^musl1779]`. One per page, reused.
- «…» quotations are copied from a snippet, whole. Otherwise paraphrase without guillemets.
- Ṣaḥīḥayn precedence: where a `K`/`M` entry covers the event, give its wording and present the other as
  "in another report".
- Links: check names before writing, and copy the spelling it prints:
  ```bash
  python3 audit.py --exists "Saʿd b. Muʿādh" "Banū Qurayẓah"
  ```
  Leave names without a note as plain text. Do not link a person the ledger does not identify
  (a bare "Bashīr b. ʿAbd al-Mundhir" is not thereby "Abū Lubābah").
- Frontmatter: keep the old keys that the entries support, with values corrected from the entries; drop
  values no entry supports. Infobox keys are those in `FIELDS` in `site_nav.py`. Keep the tags, `unverified`
  included.
- Body: `# Title (Arabic)`, an italic epithet line, a sourced lead paragraph, plain `##` sections in
  chronological order, prose paragraphs (lists only for real lists), a disputes section,
  `## References` listing only the canonical books cited, then the footnote definitions.
- **Write for a reader, not as a list of entries.** The note is an encyclopedia article, not the ledger
  in English:
  - connect sentences into paragraphs; weave a gloss into the sentence that needs it ("Safawān, a valley
    on the side of Badr") rather than giving it a sentence of its own; drop glosses the story does not need;
  - when every sentence of a paragraph rests on the same page, footnote the paragraph once, at its end;
  - a dispute is told once: in the narrative where it matters (the date, the deputy), or in the disputes
    section — not both, and no section that only points to another;
  - a one-page chapter makes a short note: a lead and two or three sections. Do not pad it with headings;
  - translate or explain a term on first use (*barīd*, *sawīq*) if the ledger gives the meaning; otherwise
    leave it in italics.
- No analysis, "significance" or "lessons" unless an entry gives them as the author's own.
- Honorific ligatures agree in gender and number (﵁ ﵂ ﵃ ﵄ ﵅ ﵊).

Write the file once with the Write tool, then correct with targeted edits.

## 3. Self-check

Go through the draft sentence by sentence and point to the entry behind each. Remove or fix any sentence
with none. Common slips:

- a `qīla` or `hedge` entry written as fact; one side of a `khilāf`;
- a detail moved to another person or occasion; two entries merged into one story;
- a connective or detail the entries do not give: "so", "because", "then", "first", "on the way back",
  "the next morning", "immediately", "the people *of Madinah*";
- an attribution stretched: a date or detail credited to an authority whose entry does not contain it;
- a flourish: "elite", "fearless", "at full gallop", "catastrophic";
- a year, kunyah, nasab or place identification supplied from general knowledge;
- a frontmatter value that merges two descriptions the entries keep apart;
- a framing sentence with no footnote.

## 4. Audit

```bash
python3 audit.py --note "<name>"     # resolve every flag
python3 audit.py --ledger
python3 audit.py --no-content        # structural checks must pass
```

For each flag, fix the claim, fix the citation, or state why it is a false positive (known ones:
al-Wāqidī printed as "Muḥammad b. ʿUmar"; English exonyms; small numbers written as words; Qurʾān verse
numbers; a name on the next page of a range). An unflagged line is not thereby verified.

## 5. Sweep the vault

For every claim of the old note you corrected or removed:

```bash
grep -n -i "<distinctive phrase>" *.md | grep -v "^<name>.md"
```

Fix another note only if the ledger settles it and the edit is one line; otherwise list it in the report.

## 6. Commit and report

Commit the note and any ledger you wrote or changed, following **Git workflow** in `CLAUDE.md` (branch
`drafts`, never push). Then report briefly: what the old note had wrong; what is kept as a dispute;
chapters "not yet ledgered"; problems seen in other notes; and that the note is ready for verify-note.
