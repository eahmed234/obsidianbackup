---
name: verify-note
description: Independently verify a rewritten nabiwiki (Sīrah vault) note against its claim ledgers and fix what is wrong. Use after rewrite-note, or when asked to check or verify a note's sourcing.
---

# Verify a nabiwiki note

Argument: the note's name.

You are the second reader, in a session that did not write the note. Assume nothing in the note or its
ledgers is right until you have checked it. `CLAUDE.md` holds the sourcing rules; `ledger/README.md` the
ledger format. You never change the `unverified`/`verified` tags: your work helps the user's own
verification and does not replace it.

## 1. Mechanical checks

```bash
python3 audit.py --ledger
python3 audit.py --note "<name>"
grep -l "<name>" ledger/*.md         # its ledgers (the `feeds:` lines)
```

## 2. Check the ledger entries the note uses

For each entry behind a sentence of the note, read the Arabic snippet, then its English:

- does the English say exactly what the Arabic says — no more, no less?
- is the kind right? Look for *qīla / ruwiya / yuqālu / zuʿima*, a second count or name, a verdict, a
  hedge (*mā ʿalimtu, laʿalla, aẓunnu*) that the entry marks as `plain`;
- is the tier right (`matn` vs `taḥqīq`)?
- direction and idiom: who did what to whom, before/after, passives, «لاثنتي عشرة ليلة خلت».

The snippet is guaranteed to be on the page; whether it was cut so as to change its sense is not. If a
snippet starts or ends oddly, open the page.

## 3. Check the note against the entries

For each sentence or clause — **including the italic epithet line, the lead paragraph, every frontmatter
value and any sentence without a footnote**:

- **supported** — an entry says this, at this strength;
- **overstated** — the entry says less: a `qīla` as fact, one side of a `khilāf`, a dropped verdict, an
  added adjective, timing, motive or connective;
- **misattributed** — right content, wrong page, report or person;
- **unsupported** — no entry says it. Open the cited page once (`python3 audit.py --page …`). If the page
  does say it, the ledger was incomplete: add the entry. If not, the sentence goes.

Also:

- «…» quotations match a snippet word for word;
- small additions: "first", "then", "on the way back", "of Madinah", "himself" — is each in a snippet?
- nothing from a ledger `- note:` appears as a claim or an interpretation;
- a disputed point in the frontmatter shows both sides; a reconciliation is not stated as fact;
- names are as the ledger prints them, and recurring phrases follow `ledger/GLOSSARY.md`;
- **attribution scope** — for each `via` entry, re-read the Arabic: do the authority's words really run to
  the end of the snippet, or does the author's own narrative resume? If it can be read both ways, it goes
  under **For you**;
- **readability** — glosses standing as one-sentence paragraphs, the same dispute told twice, a footnote
  after every sentence of a paragraph that rests on one page: tidy these (see "Write for a reader" in the
  rewrite-note skill). This changes wording only, never content.
- **missing dispute** — a `khilāf`, `verdict` or `qīla` entry about the subject that the note leaves out;
- **completeness of the ledger** — read in full the page with the *tanbīhāt* (or, for a Companion, the
  whole entry if it is two pages or less) and confirm no sentence lacks an entry.

## 4. Fix

Apply the fixes yourself; do not wait to be asked.

1. Correct the **ledger** first (rendering, kind, missing entry).
2. Then the **note**, with targeted edits. Missing disputes are sourced content: add them, footnoted.
3. Then any other note on that ledger's `feeds:` line that repeats the same error.
4. Re-run `--ledger`, `--note` and `--no-content`.

Leave unfixed, and list under **For you**, only what needs the user's judgement: a likely misprint, an
Arabic sentence that can be read two ways, a conflict between two of the five books.

**Record every such item in `ledger/QUESTIONS.md`**, under a `## <note name>` heading, in the form the file
shows: `- [ ]`, the entry id, the Arabic, the possible readings, and on a `now:` line what the note does
meanwhile (always the cautious reading: as printed, the narrower attribution). Carry over the `unsettled:`
items of the note's ledgers too. Do not add a question that is already there, and never tick one: only the
user rules. A question answered there (`- [x]` … `→ ruling`) is binding — apply it to the ledger and note.
A question that recurs across notes goes under `## General`, with "See General" in the note's section.

## 5. Report and commit

Write `review/<name>.verify.md` (git-ignored):

```
# Verification: <name>
Ledgers: …            Pages opened: …
Supported N · Overstated N · Misattributed N · Unsupported N · Missing disputes N · Ledger corrections N

| Where | Claim (short) | Verdict | Arabic | Fix applied |

## For you
```

List every non-supported item with the Arabic that shows it. Supported claims are summarised by section.
If a finding is a kind of error the rewrite-note or ledger self-check lists do not name, say so on a last
line, so the lists can be extended.

Commit the note, ledgers and `ledger/QUESTIONS.md` following **Git workflow** in `CLAUDE.md` (branch `drafts`, never push). End
with the summary line and the **For you** items. A clean result is a valid result: say so plainly.
