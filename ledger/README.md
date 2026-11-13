# Claim ledgers

A ledger is the result of reading one source chapter or entry **once**. Notes are then written from the
ledger, and checked against it, without the chapter being read again. One chapter usually feeds several
notes (the event, and a section in each person's note), so the reading is paid for once.

Ledgers are tracked in git and never published (`ledger` is in Quartz's `ignorePatterns`). They are working
papers, not notes: they carry no `unverified` tag and are not linked from the hub.

## File

`ledger/<book> <vol>.<first page> <subject>.md` — e.g. `S 4.174 Ghazwat al-Suwayq.md`
(`S` Subul al-Hudā, `I` al-Iṣābah, `B` al-Bidāyah, `K` al-Bukhārī, `M` Muslim).

The header gives the pages read (to the last line of the chapter), the notes it feeds, and anything the
reader could not settle. Then one entry per claim, in the order of the page.

## Entry

```
### S4.174.07 · matn · qīla
> وقيل: إن أبا سفيان فعل ذلك لمّا رجع في ليلته من عند سلّام بن مشكم
It is said that Abū Sufyān did this when he came back that night from Sallām b. Mishkam.
- note: "this" = the burning and the killing; the report differs on who did it and when.
```

- **Heading**: `<book><vol>.<page>.<nn>` · tier · kind. The id is the citation: `S4.174.07` is cited in a
  note as `[^s4.174]`. For the Ṣaḥīḥayn the id is `K3039.01` / `M1779.01`.
- **Tier**: `matn` (the author) or `taḥqīq` (the editors' footnotes). Never mixed in one entry.
- **Kind** — how firmly the page says it:
  - `plain` — stated without qualification;
  - `qīla` — *qīla, ruwiya, yuqālu, zuʿima*: reported weakly;
  - `khilāf` — two or more counts, dates, names; every side is in the entry;
  - `verdict` — the author's or a quoted authority's ruling (*al-ṣaḥīḥ, al-ashhar, wahima*…);
  - `hedge` — *mā ʿalimtu, aẓunnu, laʿalla*;
  - `via` — the author names the work or person he takes it from (*qāla fī al-Imtāʿ*);
  - `gloss` — from the *sharḥ al-gharīb*: only definitions of places, peoples and things a note may use.
    Vocalisation notes are left out.
- **`>` line**: the Arabic, **verbatim from that page**, as short as carries the claim. Words left out in
  the middle are marked ` … `. `python3 audit.py --ledger` fails if a snippet is not on its page.
- **English line(s)**: what the Arabic says and no more — no connective, timing, motive or adjective that
  is not in the snippet. Arabic idiom is rendered, not transliterated.
- **`- note:`** (optional): an ambiguity, a referent, a likely misprint. A note is the reader's remark, not
  the book's, and never enters a wiki note as a claim.

## Rules

- Every sentence of the narrative and the *tanbīhāt* gets an entry; nothing is summarised away. If a
  passage is skipped (a long poem, an isnād), say so in the header.
- One claim per entry. A sentence with a count, a date and a name is three things a writer may get wrong,
  but one entry is enough if the snippet shows all three.
- A note written from a ledger may say only what its entries say, at the strength of their kind.
- If a ledger is wrong, fix the ledger first, then every note listed under `feeds`.
