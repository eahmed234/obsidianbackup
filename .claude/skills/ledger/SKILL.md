---
name: ledger
description: Read one source chapter or entry of the nabiwiki (Sīrah vault) corpus once and record it as a claim ledger in ledger/. Use before rewriting a note whose source has no ledger, or when asked to "ledger" a chapter, entry or note.
---

# Build a claim ledger

Argument: a note name (`Ghazwat al-Suwayq`), or a source range (`S 4:174-175`, `I 7:99-100`, `K 3039`).

`CLAUDE.md` holds the sourcing rules; `ledger/README.md` holds the ledger format. Read `ledger/README.md`
and one finished ledger (`ledger/S 4.174 Ghazwat al-Suwayq.md`) before you start. This skill is the procedure.

A ledger is the only time the chapter is read. Everything a note may later say has to be in it, and nothing
may be in it that the page does not say.

## 1. Find the source and its limits

- `ls ledger/` first. If a ledger already covers these pages, stop and say so.
- Given a note name, take its `primary_source` and citations as **leads only**.
- **Events (*Subul al-Hudā*).** Write a generous range to a file and find the chapter:
  ```bash
  python3 audit.py --page S 4:170-180 --out review/src.txt
  grep -n "══════\|^الباب\|تنبيه\|شرح غريب\|بيان غريب" review/src.txt
  ```
  The chapter runs from its `الباب` heading to the next. It has a narrative, then *tanbīhāt* (dating,
  disputes, reconciliations, verdicts), then *gharīb*. Look at the first page of the next chapter too: a
  transition back is sometimes there.
- **Ṣaḥābah (*al-Iṣābah*).** The entry runs from its numbered heading to the next numbered heading. Confirm
  the name in the heading is this person, not a namesake.
- **Ṣaḥīḥayn.** For each report the matn names («رواه البخاري») or the taḥqīq numbers, and that the chapter
  relies on: `python3 audit.py --page K 3039 --out review/k3039.txt`. Its entries go in the same ledger,
  under a `## Ṣaḥīḥayn` heading, with ids `K3039.01`, `M1779.01`. Ledger only the reports that bear on
  this chapter's subject.
- Print with `--out` and read the file with the Read tool. Never print the same pages twice.

## 2. Read and record

Read every page to its last line (pages often open with the tail of the previous section). Write the
ledger as you go, in page order, under plain `##` headings that follow the chapter's own divisions.

- Every sentence of the narrative and of the *tanbīhāt* gets an entry. Do not summarise.
- **Copy the Arabic from the file; do not retype it from memory.** Keep each snippet as short as carries the
  claim; mark words left out in the middle with ` … `.
- Give each entry its tier (`matn` / `taḥqīq`) and its kind (`plain`, `qīla`, `khilāf`, `verdict`, `hedge`,
  `via`, `gloss`). A *khilāf* entry holds every side. A verdict names whose it is: the author's own, or
  the one he quotes.
- *Gharīb*: keep only definitions of places, peoples and things. Leave out vocalisation notes.
- Long poetry and bare isnāds may be skipped; say so in the header (`skipped:`).
- Anything you cannot settle (a likely misprint, an unclear referent) goes in a `- note:` and in the
  header's `unsettled:` line. Do not resolve it by guessing.
- **Long chapters** (more than about 25 pages): split at the chapter's own sections into parts
  (`S 4.363a …`, `S 4.363b …`), one file each. Finish and save one part before reading the next.

## 3. Check the English against the Arabic

Re-read each entry: snippet, then rendering. The rendering says what the snippet says and no more.

- a hedge kept as a hedge: «ما علمت أن أحدا…» is "he knew of no one…", not "no one…";
- a passive kept passive: «وجُمع» is "they have been reconciled", with no reconciler named;
- who did what to whom; who asked and who answered;
- "before"/"after" and what follows "because" the right way round;
- date idiom: «لاثنتي عشرة ليلة خلت» is "when twelve nights had passed", not "the twelfth night";
- no adjective, timing ("that morning", "immediately") or motive the snippet lacks;
- an unnamed person stays unnamed; a name the page gives without kunyah or nasab gets none;
- numbers exactly as given, including "about" and "or so".

## 4. Verify and commit

```bash
python3 audit.py --ledger        # every snippet verbatim on its page — must pass
```

Fill in the header (`pages read`, `taḥqīq`, `feeds`, `skipped`, `unsettled`). Commit the ledger file only,
following **Git workflow** in `CLAUDE.md` (branch `drafts`, never push).

## 5. Report

Three lines: the file, the number of entries by kind, and the `unsettled` items.
