# Primary Canonical Corpora

This directory contains the authoritative primary source corpora for **nabiwiki**, stored as Shamela-formatted EPUB files:

1. **`1693.epub`**: *Subul al-Hudā war-Rashād fī Sīrat Khayr al-ʿIbād* (سبل الهدى والرشاد في سيرة خير العباد)
   - **Author**: Imām Muḥammad b. Yūsuf al-Ṣāliḥī al-Shāmī (d. 942 AH)
   - **Edition**: Dār al-Kutub al-ʿIlmiyyah, Beirut, 1414/1993, 12 volumes.
   - **Scope**: Canonical narrative, military expeditions (*maghāzī* & *sarāyā*), geography, delegations (*wufūd*), and prophetic virtues.
   - **Citation format**: `*Subul al-Hudā*, <vol>:<page>`

2. **`9767.epub`**: *al-Iṣābah fī Tamyīz al-Ṣaḥābah* (الإصابة في تمييز الصحابة)
   - **Author**: al-Ḥāfiẓ Ibn Ḥajar al-ʿAsqalānī (d. 852 AH)
   - **Edition**: Dār al-Kutub al-ʿIlmiyyah, Beirut, 1415/1995, 8 volumes, ed. ʿĀdil ʿAbd al-Mawjūd & ʿAlī Muʿawwaḍ.
   - **Scope**: Biographical encyclopedia of the Companions (Ṣaḥābah), genealogical chains, tribal affiliations, conversion accounts, campaigns, and death dates.
   - **Citation format**: `*al-Iṣābah*, <vol>:<page>` or `*al-Iṣābah*, no. <tarjamah> (<vol>:<page>)`

## Internal EPUB Structure
Both files use standard Shamela XHTML page files in `OEBPS/text/`:
- **Matn (Primary text)**: `<p>` and `<h3>`, `<h4>`, `<h5>` tags.
- **Taḥqīq (Footnotes / Apparatus)**: `<p class="hamesh">...</p>`.
- **Volume / Page Indicator**: `<p class="text-center">الجزء: X - الصفحة: Y</p>`.

These files are read directly by `audit.py`: it checks that every cited volume:page exists, compares each
claim in a note against the Arabic text of the pages it cites (numbers, transliterated names, «…» quotations),
and prints pages on demand — `python3 audit.py --page S 6:77-78` (S = Subul al-Hudā, I = al-Iṣābah).
