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

3. **`4445.epub`**: *al-Bidāyah wa-l-Nihāyah* (البداية والنهاية)
   - **Author**: Ibn Kathīr (d. 774 AH)
   - **Edition**: ed. ʿAbdullāh b. ʿAbd al-Muḥsin al-Turkī, Dār Hajr, 1417–1419/1997–98, 21 volumes.
   - **Scope**: Only the period after the Prophet's ﷺ death — vol. 8, p. 79 onward (Abū Bakr's caliphate opens at 9:414).
   - **Citation format**: `*al-Bidāyah*, <vol>:<page>`

4. **`1681.epub`**: *Ṣaḥīḥ al-Bukhārī* (صحيح البخاري), al-Sulṭāniyyah edition
   - **Citation format**: `*Ṣaḥīḥ al-Bukhārī*, no. <ḥadīth>` — the standard numbering printed at the head of each report.

5. **`1727.epub`**: *Ṣaḥīḥ Muslim* (صحيح مسلم), ed. Muḥammad Fuʾād ʿAbd al-Bāqī
   - **Citation format**: `*Ṣaḥīḥ Muslim*, no. <ḥadīth>` — the bracketed general number in «١٣٠ - (٧٦)», i.e. 76.

## Internal EPUB Structure
All five files use standard Shamela XHTML page files in `OEBPS/text/`:
- **Matn (Primary text)**: `<p>` and `<h3>`, `<h4>`, `<h5>` tags.
- **Taḥqīq (Footnotes / Apparatus)**: `<p class="hamesh">...</p>`.
- **Volume / Page Indicator**: `<p class="text-center">الجزء: X - الصفحة: Y</p>`.

These files are read directly by `audit.py`: it checks that every cited volume:page and ḥadīth number exists, compares each
claim in a note against the Arabic text of the pages it cites (numbers, transliterated names, «…» quotations),
and prints pages on demand — `python3 audit.py --page S 6:77-78` (S = Subul al-Hudā, I = al-Iṣābah,
B = al-Bidāyah) or `python3 audit.py --page K 3039` (K = al-Bukhārī, M = Muslim, by ḥadīth number).
