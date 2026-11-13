# Open questions for the verifier

Points the ledger, rewrite and verify sessions could not settle and left for the user's own reading. They
are collected here so they are in front of you when you verify a note: `python3 audit.py --sheet "<note>"`
prints that note's questions at the top of its sheet, and `python3 audit.py --questions` lists every note
that has any.

- One `## <note name>` section per note (the file name without `.md`); `## General` for questions that
  recur across notes.
- An open question is `- [ ]`. When you rule, change it to `- [x]` and write the ruling after `→`. A ruling
  that will recur (a name, a phrase, a tagging rule) is also recorded in `ledger/GLOSSARY.md`.
- Until a question is answered, the note follows the cautious reading stated under "now:".

## General

- [ ] **«أبو عمرو» beside Ibn Ḥazm / Ibn Hishām** (*Subul* 4:15, 4:17; «أبو عمر» at 4:176). Misprint for Abū ʿUmar?
  now: written "Abū ʿAmr", as printed. →
- [ ] **Hijrī-year tags.** When a page gives only "N months from his hijrah" and no year, may a note carry a year tag (`2-ah`) as arithmetic, like the Gregorian exemption?
  now: existing tags kept, none added. →

## Ghazwat Safawān

- [ ] **S4.16.02 — where Ibn Ḥazm's words end.** «وقال ابن حزم: بعدها بعشرة أيام خرج رسول الله ﷺ في ربيع الأول على رأس ثلاثة عشر شهرا … من مهاجره». Either all of it is Ibn Ḥazm's, or his words end at «بعشرة أيام» and the date is al-Ṣāliḥī's own narrative (Rabīʿ al-Awwal at thirteen months cannot follow al-ʿUshayrah, which 4:17 puts in Jumādā at sixteen months).
  now: the note and `date_hijri` credit the date to Ibn Ḥazm. →
- [ ] **S4.16.02 — the ellipsis** printed between «ثلاثة عشر شهرا» and «من مهاجره»: the page does not say what is omitted.
  now: read as "thirteen months from the hijrah". →

## Ghazwat Buwāṭ

- [ ] **S4.15.01, S4.15.04 — «أبو عمرو».** See General.
  now: "Abū ʿAmr". →
- [ ] **Tag `2-ah`.** The page gives "thirteen months from his hijrah" and no year. See General.
  now: tag kept. →

## Ghazwat al-ʿUshayrah

- [ ] **S4.17.04–.12 — where the Ibn Isḥāq / Ibn Ḥazm quotation ends.** «وقال ابن إسحاق وابن حزم وغيرهما: في جمادى الأولى، وحمل لواءه … واستخلف … وخرج في مائة وخمسين، ويقال في مائتين». The sentence runs on from the date into the banner, deputy and numbers; either all is theirs or only the date.
  now: the date is credited to them by name; banner, deputy and numbers are written as plain narrative. →
- [ ] **S4.17.13–.16 — where Abū ʿAmr's words end.** «قال أبو عمرو: أخذ … على طريق ملل إلى العشيرة، فأقام … ووادع … ثم رجع إلى المدينة ولم يلق كيدا، قالوا: …». Is the whole route/stay/truce/return his, or only the first clause? (See General on «أبو عمرو».)
  now: written as plain narrative, no attribution in the text. →
- [ ] **S4.17.17 — «قالوا».** Who "they" are is not stated.
  now: "It is said that…". →

## Ghazwat al-Suwayq

- [ ] **S4.174.06 — «فبعث رجلًا من قريش فأتوا…».** Singular «رجلًا» with plural verbs after it.
  now: rendered "men". →
- [ ] **S4.174.09 — «وقيل: إن أبا سفيان فعل ذلك».** What «ذلك» refers to (most likely the raid on al-ʿUrayḍ).
  now: the note gives the report in the source's words without interpreting it. →
- [ ] **Tag `2-ah`.** The page gives «على رأس اثنين وعشرين شهرا» without saying from what, and no year. See General.
  now: tag kept. →
