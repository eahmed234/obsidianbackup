#!/usr/bin/env python3
"""
audit.py — integrity and source-verification triage for nabiwiki.

Structural checks (these set the exit code):
  1. Citation bounds   every cited vol:page of Subul al-Hudā / al-Iṣābah exists in the EPUB.
  2. Hub completeness  every note is linked from The Sīrah.md.
  3. Wrapped links     no wikilink contains a line break.
  4. Frontmatter       title / arabic / type / tags present; primary_source on content notes.
  5. Link integrity    unresolved wikilink targets (informational: eager links are by design).
  6. Alias collisions  no name (alias, or extra search name in site_search.json) is claimed by two
                       notes unless site_search.json settles it ("primary" or "ambiguous").

Content triage (informational — a list for a human to look at, never a verdict):
  Each line of a note is split at its citations; the text before a citation is a
  "claim", and it is checked against the Arabic text of the pages it cites.
  7. numbers     numerals in the claim that appear on none of the cited pages
                 (Arabic-Indic / Western digits and Arabic number words).
  8. terms       transliterated names / terms whose consonantal skeleton is absent
                 from the cited pages.
  9. quotes      Arabic «…» quotations not found on the cited pages.
 10. apparatus   a term found only in the taḥqīq of a page cited as matn.
 11. uncited     substantive prose lines carrying no citation to either book.
 12. other-work  direct citations of works other than the two canonical books.
 A missing item that does occur within a few pages of the citation is reported with
 "found at V:P" — the typical signature of a close-but-wrong citation.

Usage:
  python3 audit.py                     summary of everything
  python3 audit.py --note "Abū Dujānah"  full findings for one note
  python3 audit.py --content           full findings for every note
  python3 audit.py --report review/_triage.md   write the full triage as Markdown
  python3 audit.py --sheet "Sariyyat al-Ghamr"  write a source sheet for a human verifier
  python3 audit.py --page S 6:77-78    print cited pages (S = Subul al-Hudā, I = al-Iṣābah, B = al-Bidāyah)
  python3 audit.py --page K 3039       print a ḥadīth by number (K = al-Bukhārī, M = Muslim)
  python3 audit.py --links             list every unresolved wikilink
  python3 audit.py --citations         list every out-of-bounds citation
  python3 audit.py --reindex           rebuild the EPUB page index cache
"""

import argparse
import builtins
import glob
import html
import json
import math
import os
import re
import sys
import zipfile
import difflib
from collections import Counter, defaultdict

VAULT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_DIR = os.path.join(VAULT_DIR, "sources")
REVIEW_DIR = os.path.join(VAULT_DIR, "review")
CACHE_FILE = os.path.join(SOURCES_DIR, ".index_cache.json")
NON_NOTES = {"GEMINI.md", "CLAUDE.md", "README.md", "AGENTS.md"}
SEARCH_CFG = os.path.join(VAULT_DIR, "site_search.json")   # search names and alias rulings (see site_search.py)

# The canonical sources (see CLAUDE.md, "Sourcing rules"). kind "page" is cited vol:page;
# kind "hadith" is cited by ḥadīth number.
SOURCES = {
    "S": {"label": "Subul al-Hudā", "file": "1693.epub", "kind": "page", "key": "subul"},
    "I": {"label": "al-Iṣābah", "file": "9767.epub", "kind": "page", "key": "isabah"},
    "B": {"label": "al-Bidāyah", "file": "4445.epub", "kind": "page", "key": "bidayah"},
    "K": {"label": "Ṣaḥīḥ al-Bukhārī", "file": "1681.epub", "kind": "hadith", "key": "bukhari"},
    "M": {"label": "Ṣaḥīḥ Muslim", "file": "1727.epub", "kind": "hadith", "key": "muslim"},
}
BOOK_LABEL = {k: v["label"] for k, v in SOURCES.items()}
# al-Bidāyah (ed. al-Turkī) is a source only for what follows the Prophet's ﷺ death: vol. 8, p. 79
# ("events after his death and before his burial") onward. Earlier pages are out of scope.
BIDAYAH_FROM = (8, 79)
# Ḥadīth number at the start of a report: al-Bukhārī "٦٨٨٧ - …"; Muslim (ʿAbd al-Bāqī) "١٣٠ - (٧٦) …",
# where the bracketed number is the standard one.
HADITH_START = {
    "K": re.compile(r"^([٠-٩]+)\s*-"),
    "M": re.compile(r"^(?:[٠-٩]+\s*-\s*)?\(([٠-٩]+)\)"),
}
BROAD_RANGE = 12          # a citation spanning more pages than this is not content-checked
NEAR = 3                  # how far either side of a citation to look for a "found at" hint

PAGE_RE = re.compile(r"الجزء:\s*(\d+)\s*-\s*الصفحة:\s*(\d+)")


# ════════════════════════════════════════════════════════════════════════════
#  EPUB corpora
# ════════════════════════════════════════════════════════════════════════════

def _mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return 0


INDEX_FORMAT = 3   # bump to force a rebuild of .index_cache.json when the index layout changes


def _file_order(fname):
    """Sort key putting Shamela's page_<part>_<seq>.xhtml files in reading order."""
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", fname)]


def build_epub_index(epub_path, name, book=None):
    if not os.path.isfile(epub_path):
        print(f"Warning: {epub_path} not found. Skipping {name} index.")
        return {}
    print(f"Indexing {name} from {os.path.basename(epub_path)}...")
    index, vol_max, ordered = {}, {}, []
    with zipfile.ZipFile(epub_path) as z:
        # Shamela often splits one printed page over several files (in the Ṣaḥīḥayn, roughly one per
        # report or heading), each carrying the same page marker. Keep every file, in reading order.
        names = sorted((n for n in z.namelist() if n.startswith("OEBPS/text/")), key=_file_order)
        for fname in names:
            data = z.read(fname).decode("utf-8", errors="ignore")
            m = PAGE_RE.search(data)
            if m:
                v, p = int(m.group(1)), int(m.group(2))
                index.setdefault(f"{v}:{p}", []).append(fname)
                vol_max[v] = max(vol_max.get(v, 0), p)
                ordered.append((v, p, data))
    out = {"pages": index, "max_pages": vol_max, "mtime": _mtime(epub_path), "format": INDEX_FORMAT}
    if book in HADITH_START:
        # ḥadīth number → the pages it occupies (from its first page to the page before the next number)
        rx, digits = HADITH_START[book], str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        hadith, current = {}, None
        for v, p, data in sorted(ordered, key=lambda x: (x[0], x[1])):
            key = f"{v}:{p}"
            if current and key not in hadith[current] and len(hadith[current]) < 6:
                hadith[current].append(key)
            for para in re.findall(r"<p(?![^>]*hamesh)[^>]*>(.*?)</p>", data, re.S):
                t = html.unescape(re.sub(r"<[^>]+>", "", para)).strip()
                hm = rx.match(t)
                if hm:
                    current = str(int(hm.group(1).translate(digits)))
                    pages = hadith.setdefault(current, [key])
                    if key not in pages:              # a sub-report of the same number further on (Muslim)
                        pages.append(key)
        out["hadith"] = hadith
    return out


def load_or_build_indices(force=False):
    cache = {}
    if os.path.isfile(CACHE_FILE) and not force:
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}
    updated = False
    for code, src in SOURCES.items():
        key, path = src["key"], os.path.join(SOURCES_DIR, src["file"])
        c = cache.get(key, {})
        if not (c.get("mtime") == _mtime(path) and c.get("pages") and c.get("format") == INDEX_FORMAT):
            cache[key] = build_epub_index(path, src["label"], code)
            updated = True
    if updated:
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except Exception as e:
            print(f"Warning: could not save index cache: {e}")
    return {code: cache.get(src["key"], {}) for code, src in SOURCES.items()}


def make_corpora(indices):
    corp = {}
    for code, src in SOURCES.items():
        corp[code] = Corpus(code, os.path.join(SOURCES_DIR, src["file"]), indices.get(code, {}))
        HADITH_INDEX[code] = corp[code].hadith
    return corp


class Corpus:
    """Lazy page reader for one EPUB. Splits each page into matn and taḥqīq (hamesh)."""

    def __init__(self, book, epub_path, index):
        self.book = book
        self.path = epub_path
        self.pages = index.get("pages", {})
        self.hadith = index.get("hadith", {})
        self._zip = None
        self._raw = {}
        self._norm = {}

    def has(self, vol, page):
        return f"{vol}:{page}" in self.pages

    def raw(self, vol, page):
        """(matn, tahqiq) as readable text, or None."""
        key = f"{vol}:{page}"
        if key in self._raw:
            return self._raw[key]
        fnames = self.pages.get(key)
        if not fnames:
            self._raw[key] = None
            return None
        if isinstance(fnames, str):
            fnames = [fnames]
        if self._zip is None:
            self._zip = zipfile.ZipFile(self.path)
        data = "\n".join(self._zip.read(f).decode("utf-8", errors="ignore") for f in fnames)
        matn, tahqiq = [], []
        for m in re.finditer(r"<(p|h\d)([^>]*)>(.*?)</\1>", data, re.S):
            txt = html.unescape(re.sub(r"<[^>]+>", " ", m.group(3)))
            txt = re.sub(r"[ \t]+", " ", txt).strip()
            if not txt or PAGE_RE.search(txt) or txt.startswith("كتاب سبل الهدى"):
                continue
            (tahqiq if "hamesh" in m.group(2) else matn).append(txt)
        self._raw[key] = ("\n".join(matn), "\n".join(tahqiq))
        return self._raw[key]

    def norm(self, vol, page):
        """(matn, tahqiq) normalised for skeleton matching, plus number sets."""
        key = f"{vol}:{page}"
        if key not in self._norm:
            r = self.raw(vol, page)
            if r is None:
                self._norm[key] = None
            else:
                self._norm[key] = {
                    "matn": ar_skeleton(r[0]), "tahqiq": ar_skeleton(r[1]),
                    "matn_words": ar_words(r[0]), "tahqiq_words": ar_words(r[1]),
                    "nums": arabic_numbers(r[0] + "\n" + r[1]),
                }
        return self._norm[key]


# ════════════════════════════════════════════════════════════════════════════
#  Arabic normalisation, numbers, transliteration → skeleton
# ════════════════════════════════════════════════════════════════════════════

_TASHKIL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")


def ar_norm_word(s):
    s = _TASHKIL.sub("", s)
    s = re.sub("[أإآٱ]", "ا", s)
    s = s.replace("ؤ", "و").replace("ئ", "ي").replace("ء", "").replace("ى", "ي").replace("ة", "ه")
    return s


def ar_skeleton(text):
    """Arabic letters only, no spaces, doubled letters collapsed."""
    s = ar_norm_word(text)
    s = re.sub(r"[^ء-ي]", "", s)
    return re.sub(r"(.)\1+", r"\1", s)


def ar_words(text):
    return [re.sub(r"(.)\1+", r"\1", w) for w in re.findall(r"[ء-ي]+", ar_norm_word(text))]


_AR_NUM = {}
for _v, _ws in {
    1: "واحد واحده احد احدي حادي اول اولي", 2: "اثنان اثنين اثنا اثني اثنتان اثنتين اثنتا اثنتي ثاني ثانيه",
    3: "ثلاث ثلاثه ثالث ثالثه ثلث", 4: "اربع اربعه رابع رابعه", 5: "خمس خمسه خامس خامسه",   # ثلث = "a third"
    6: "ست سته سادس سادسه", 7: "سبع سبعه سابع سابعه", 8: "ثمان ثماني ثمانيه ثامن ثامنه",
    9: "تسع تسعه تاسع تاسعه", 10: "عشر عشره عاشر عاشره",
    20: "عشرون عشرين", 30: "ثلاثون ثلاثين", 40: "اربعون اربعين", 50: "خمسون خمسين",
    60: "ستون ستين", 70: "سبعون سبعين", 80: "ثمانون ثمانين", 90: "تسعون تسعين",
    100: "مايه ميه", 200: "مايتان مايتين مايتي مايتا ميتان ميتين",
    300: "ثلاثمايه ثلثمايه", 400: "اربعمايه", 500: "خمسمايه", 600: "ستمايه", 700: "سبعمايه",
    800: "ثمانمايه ثمانيمايه", 900: "تسعمايه", 1000: "الف الفا الاف الوف", 2000: "الفان الفين الفي",
}.items():
    for _w in _ws.split():
        _AR_NUM[_w] = _v
_AR_PREFIXES = ("وال", "بال", "فال", "لل", "ال", "و", "ف", "ب", "ل", "ك")


def _ar_num_value(w):
    if w in _AR_NUM:
        return _AR_NUM[w]
    for p in _AR_PREFIXES:
        if w.startswith(p) and w[len(p):] in _AR_NUM:
            return _AR_NUM[w[len(p):]]
    return None


def arabic_numbers(text):
    """Every number expressible from the page: digits, number words, and compounds."""
    out = set()
    t = text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    for d in re.findall(r"\d+", t):
        out.add(int(d))
    words = re.findall(r"[ء-ي]+", ar_norm_word(t))
    total = cur = 0
    in_seq = False
    for w in words:
        base = w[1:] if w.startswith("و") and len(w) > 2 and _ar_num_value(w[1:]) is not None else w
        v = _ar_num_value(base)
        if v is None:
            if in_seq:
                out.add(total + cur)
            total = cur = 0
            in_seq = False
            continue
        in_seq = True
        out.add(v)
        if v == 1000:
            total += (cur or 1) * 1000
            cur = 0
        elif v == 2000:
            total += 2000
            cur = 0
        elif v == 100:
            cur = (cur or 1) * 100
        else:
            cur += v
        out.add(total + cur)
    if in_seq:
        out.add(total + cur)
    return out


_EN_NUM = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
    "fifteen sixteen seventeen eighteen nineteen".split())}
_EN_NUM.update({"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
                "seventy": 70, "eighty": 80, "ninety": 90})
_EN_ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7,
           "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12}

_STRIP_FOR_NUMBERS = [
    re.compile(r"\d+\s*:\s*\d+(?:\s*[–-]\s*\d+)?"),                     # Qurʾān / vol:page refs
    re.compile(r"\b(?:no|n|entry|vol|vols|pp?|āyah|ayah|āyāt|verses?)\.?\s*\d+(?:\s*[–-]\s*\d+)?", re.I),
    re.compile(r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|"
               r"November|December)\b"),                                # Gregorian day-month: exempt
    re.compile(r"[~c.]*\d{3,4}\s*(?:–\s*\d{3,4}\s*)?(?:CE|BCE|AD)\b"),   # Gregorian: exempt
    re.compile(r"\b\d{3,4}/\d{3,4}\b"),                                 # 1414/1993
    re.compile(r"\[\[[^\]]*\]\]"),
]


def english_numbers(text):
    """Numbers asserted in an English claim (value 1 is ignored: too common to be informative)."""
    t = text
    for rx in _STRIP_FOR_NUMBERS:
        t = rx.sub(" ", t)
    t = re.sub(r"(?m)^[\s>*\-]*\d+\.\s", " ", t)          # list numbering
    found = set()
    for m in re.finditer(r"\b(\d{1,3}(?:,\d{3})+|\d+)(?:st|nd|rd|th)?\b", t):
        found.add(int(m.group(1).replace(",", "")))
    toks = re.findall(r"[a-z]+|[^\sa-z]", t.lower().replace("-", " "))   # punctuation breaks a number
    total = cur = 0
    in_seq = False
    for w in toks + ["."]:
        if w in _EN_NUM:
            cur += _EN_NUM[w]; in_seq = True
        elif w in _EN_ORD:
            found.add(_EN_ORD[w])
        elif w == "hundred" and in_seq:
            cur = (cur or 1) * 100
        elif w == "thousand" and in_seq:
            total += (cur or 1) * 1000; cur = 0
        elif w == "and" and in_seq and cur % 100 == 0 and cur:
            continue                                     # "two hundred and five"
        else:
            if in_seq:
                found.add(total + cur)
            total = cur = 0; in_seq = False
    found.discard(0); found.discard(1)
    return found


# — transliteration —

_DIACRITICS = set("āīūḥṣḍṭẓĀĪŪḤṢḌṬẒʿʾʻ")
_AYN = "ʿʻ‘"
_HAMZA = "ʾ’'"
_LETTERS = {
    "th": "ث", "kh": "خ", "dh": "ذ", "sh": "ش", "gh": "غ",
    "b": "ب", "t": "ت", "j": "ج", "ḥ": "ح", "d": "د", "r": "ر", "z": "ز", "s": "س", "ṣ": "ص",
    "ḍ": "ض", "ṭ": "ط", "ẓ": "ظ", "f": "ف", "q": "ق", "k": "ك", "l": "ل", "m": "م", "n": "ن",
    "h": "ه", "w": "و", "y": "ي", "ī": "ي", "ū": "و", "g": "ج", "v": "ف", "p": "ب", "x": "كس",
}
_SUN_ARTICLE = r"(?:l|t|th|d|dh|r|z|s|sh|ṣ|ḍ|ṭ|ẓ|n)"
EXONYMS = {
    "medina": "مدينه|يثرب", "mecca": "مكه", "syria": "شام", "levant": "شام", "abyssinia": "حبش",
    "abyssinian": "حبش", "yemen": "يمن", "jerusalem": "مقدس|ايليا", "iraq": "عراق", "egypt": "مصر",
    "persia": "فارس|فرس", "persian": "فارس|فرس", "persians": "فارس|فرس", "byzantine": "روم",
    "byzantines": "روم", "roman": "روم", "romans": "روم", "rome": "روم", "heraclius": "هرقل",
    "negus": "نجاشي", "jews": "يهود", "jewish": "يهود", "christian": "نصار|نصران",
    "christians": "نصار|نصران", "magians": "مجوس", "zoroastrian": "مجوس", "ethiopia": "حبش",
    "jordan": "اردن", "antioch": "انطاكي", "constantinople": "قسطنطيني", "damascus": "دمشق",
    "homs": "حمص", "kaaba": "كعبه", "yarmouk": "يرموك", "persians'": "فارس|فرس",
}
# Vocabulary used editorially in English prose; never checked as a claimed source term.
GENERIC = set("""
hudā iṣābah ṣāliḥī ḥajar ṣaḥābah ṣaḥābī ṣaḥābiyyah tamyīz ʿasqalānī qurʾān qurʾānic ṣaḥīḥ ṣaḥīḥayn
rashād sīrah sīrat sūrat sūrah imām bāb kitāb ʿilmiyyah ḥāfiẓ ʿibād muʿawwaḍ mawjūd ʿādil jāhiliyyah
maghāzī ḥadīth aḥādīth nuzūl asbāb faḍāʾil taḥqīq matn ʿalayhi raḍiya salām ṣallā sunnī shāfiʿī
ḥijrī hijrī dīn khilāfah ummah sharīʿah fiqh ʿulamāʾ tafsīr āyah āyāt isnād sanad ghazwah ghazwat
ghazawāt sariyyah sariyyat sarāyā jihād shahīd shuhadāʾ allāh allāh's ﷺ khayr iṣṭilāḥ tanbīh
tanbīhāt muqaddimah sharḥ ʿilm madhhab mujtahid muḥaddith muḥaddithūn amīr khalīfah tarjamah prophet prophet's prophets messenger rasūl rasūlillāh islam islamic muslim muslims quran hijrah hijrī nubuwwah risālah
""".split())
# Epithets that distinguish a title in English but are routinely absent from the page that narrates it.
TOLERATED = set("""
al-kubrā al-ṣughrā al-ʿuẓmā al-ūlā al-thāniyah al-thālithah al-munawwarah al-mukarramah al-nabawī
al-ḥarām al-sharīf al-ṣiddīq al-fārūq al-zahrāʾ al-ṭayyār
""".split())
WEAK = set("""
abū abī abā umm banū banī b. b bint ibn bin dhū dhī dhā dhāt ʿabd al wa fī ilā ʿalā min ʿan yawm
bayʿat jabal wādī biʾr dār ahl ʿām wafd masjid
""".split())
EN_STOP = set("""
the of and to a an in is was that his her he she it you we they with for on by from as at this be are
not who which or o my your our their them him me us i what when if then so but no will shall have has had
""".split())


def translit_regex(word, vocalized=False):
    """IJMES word → regex over the Arabic skeleton (None if too short to be informative)."""
    w = word.lower().strip("*_.,;:()\"“”[]!?«»")
    w = re.sub(r"(?:'|’)s$", "", w)
    if not w or w in GENERIC:
        return None
    if w in EXONYMS:
        return "(?:" + EXONYMS[w] + ")"
    if w in ("b.", "ibn", "bin", "b"):
        return "ا?بن"
    pre = ""
    m = re.match(r"^wa" + _SUN_ARTICLE + r"-", w)
    if m:
        pre, w = "و(?:ال)?", w[m.end():]
    else:
        m = re.match(r"^(?:a|e)" + _SUN_ARTICLE + r"-", w)
        if m:
            pre, w = "(?:ال)?", w[m.end():]
        else:
            m = re.match(r"^(bi|li|wa|fa|bil|lil)-", w)
            if m:
                pre = {"bi": "ب", "li": "ل", "wa": "و", "fa": "ف", "bil": "بال", "lil": "ل"}[m.group(1)]
                w = w[m.end():]
    if w in GENERIC:
        return None
    w = w.replace("-", "")
    if vocalized:                                  # i‘rāb endings in a transliterated Arabic phrase
        w = re.sub(r"(?<=[^aiuāīū])an$", "ā", w)
        w = re.sub(r"(?<=[^aiuāīū])[ui]n$", "", w)
    w = re.sub(r"^miʾat", "māʾt", w)               # مائة / مائتي: orthographic alif
    plural = bool(re.search(r"(?<=[^aiuāīū])(?:ūn|īn)$", w)) and len(w) > 5
    if plural:                                     # sound plural: -ūn / -īn by case
        w = w[:-2]
    suffix = ""
    m = re.search(r"[aiu]?llāh$", w)
    if m:
        w, suffix = w[:m.start()], "اله"
        if not w:
            return pre + suffix
    units = []          # list of (literal_letter or None, regex)
    i, start = 0, True
    while i < len(w):
        two = w[i:i + 2]
        ch = w[i]
        last = i == len(w) - 1
        if two in _LETTERS and len(two) == 2:
            units.append((_LETTERS[two], _LETTERS[two])); i += 2; start = False; continue
        if ch in _AYN:
            units.append(("ع", "ع"))
        elif ch in _HAMZA:
            units.append((None, "[اوي]?"))      # hamza seat: أ / ؤ / ئ normalise to ا / و / ي
        elif ch == "ā":
            units.append((None, "ا" if start else ("[اي]" if last else "ا?")))
        elif ch in "aiueo":
            if start:
                units.append(("ا", "ا"))
            elif last and ch == "a":
                units.append((None, "[اه]?"))
        elif ch == "t" and last:
            units.append((None, "[ته]"))
        elif ch in _LETTERS:
            units.append((_LETTERS[ch], _LETTERS[ch]))
        else:
            return None
        start = False
        i += 1
    rx, prev, core = [], None, 0
    for lit, r in units:
        if lit is not None and lit == prev:
            continue
        rx.append(r)
        prev = lit
        if lit is not None or r in ("[ته]",):
            core += 1
    core += 2 if suffix else 0
    if plural:
        rx.append("[وي]ن")
    if core < 2 or (core == 2 and len(rx) < 3):
        return None
    return pre + "".join(rx) + suffix


def is_arabicish(tok, name_words):
    low = tok.lower().strip("*_.,;:()\"“”[]!?")
    if any(c in _DIACRITICS for c in tok):
        return True
    if re.match(r"^(?:wa)?(?:a|e)" + _SUN_ARTICLE + r"-\w", low):
        return True
    if low in EXONYMS:
        return True
    return tok[:1].isupper() and low in name_words


# ════════════════════════════════════════════════════════════════════════════
#  Citation parsing
# ════════════════════════════════════════════════════════════════════════════

ANCHOR_RE = re.compile(r"Subul al-Hud[āa]|al-I[ṣs][āa]bah|al-Bid[āa]yah|Ṣaḥīḥ al-Bukhārī|Ṣaḥīḥ Muslim|\(vol\.", re.I)
OTHER_WORK_RE = re.compile(
    r"Qurʾān|Qur'an|\bQ\.\s*\d|Sūra[th]?\b|Ṣaḥīḥ(?! al-Bukhārī| Muslim)|Sunan|Musnad|Tārīkh|Ṭabaqāt|Ibn Hishām|Rawḍ al-Unuf|"
    r"Dalāʾil|Mustadrak|Muwaṭṭaʾ|Jāmiʿ|Fatḥ al-Bārī|Usd al-Ghābah|Istīʿāb|ʿUyūn al-Athar|Maghāzī|"
    r"Zād al-Maʿād|Sharḥ|Muṣannaf|Tafsīr")
_T_VP = re.compile(r"(\d+)\s*:\s*(\d+)(?:\s*[–-]\s*(\d+))?")
_T_VOL = re.compile(r"\bvol(?:ume)?s?\.?\s*(\d+)\b", re.I)
_T_PP = re.compile(r"\bpp?\.\s*((?:\d+(?:\s*[–-]\s*\d+)?)(?:\s*,\s*\d+(?:\s*[–-]\s*\d+)?(?!\s*:))*)", re.I)
_T_NO = re.compile(r"\b(?:entr(?:y|ies)\s*(?:nos?\.?)?|nos?\.?)\s*(\d+)(?:\s*(?:,|and|&)\s*\d+(?!\s*:))*", re.I)
_T_NOTE = re.compile(r"\bn\.\s*(\d+)|taḥqīq", re.I)
_T_HADITH = re.compile(r"[\s*,:]*(?:ḥadīth\s+)?(?:nos?\.?\s*)?(\d+(?:\s*(?:,|and|&)\s*\d+)*)", re.I)
_T_CONT = re.compile(r",\s*(\d+)(?:\s*[–-]\s*(\d+))?(?=\s*(?:[,;)\]|.\"]|$|\(|n\.|\*))")


HADITH_INDEX = {}   # book → {ḥadīth number: [vol:page, …]}; filled when the corpora are loaded


class Citation:
    __slots__ = ("book", "refs", "start", "end", "tahqiq", "entries", "text", "numbers")

    def __init__(self, book, start):
        self.book, self.start = book, start
        self.refs = []          # (vol, first, last)
        self.tahqiq = False
        self.entries = []
        self.numbers = []       # ḥadīth numbers, for the Ṣaḥīḥayn
        self.end = start
        self.text = ""

    def pages(self):
        if self.numbers:
            out = []
            for n in self.numbers:
                for key in HADITH_INDEX.get(self.book, {}).get(str(n), []):
                    v, p = key.split(":")
                    out.append((int(v), int(p)))
            return out
        out = []
        for v, a, b in self.refs:
            if b - a <= BROAD_RANGE:
                out.extend((v, p) for p in range(a, b + 1))
        return out

    def broad(self):
        return any(b - a > BROAD_RANGE for _, a, b in self.refs)

    def label(self):
        if self.numbers:
            return f"{BOOK_LABEL[self.book]} no. " + ", ".join(map(str, self.numbers))
        parts = []
        for v, a, b in self.refs:
            parts.append(f"{v}:{a}" + (f"–{b}" if b != a else ""))
        return f"{BOOK_LABEL[self.book]} " + ", ".join(parts) + (" (taḥqīq)" if self.tahqiq else "")


def parse_citations(line):
    """All canonical citations in one line, in order, with their character spans."""
    cites = []
    anchors = []
    for a in ANCHOR_RE.finditer(line):
        # "(vol." directly after a named book belongs to that book, not to the bare Subul shorthand
        if a.group(0).lower().startswith("(vol") and anchors:
            gap = line[anchors[-1].end():a.start()]
            if len(gap) < 80 and "(" not in gap and ")" not in gap:
                continue
        anchors.append(a)
    for k, a in enumerate(anchors):
        s = a.group(0).lower()
        book = ("S" if (s.startswith("subul") or s.startswith("(vol")) else "I" if "bah" in s and "id" not in s[:6]
                else "B" if "bid" in s else "K" if "bukh" in s else "M")
        start = a.start()
        if s.startswith("(vol"):
            tail_start = a.start() + 1
        else:
            tail_start = a.end()
            # extend the span back over "(*", "[[", "*" so the claim text stays clean
            j = start
            while j > 0 and line[j - 1] in "*[ (":
                j -= 1
                if line[j] == "(":
                    break
            start = j
        limit = anchors[k + 1].start() if k + 1 < len(anchors) else len(line)
        limit = min(limit, tail_start + 700)   # long enough for an expanded footnote
        # tail stops at an unbalanced ")", a quote, a table pipe, or another work
        depth, end = 0, limit
        for i in range(tail_start, limit):
            c = line[i]
            if c == "(":
                depth += 1
            elif c == ")":
                if depth == 0:
                    end = i
                    break
                depth -= 1
            elif c in "|\"":
                end = i
                break
        tail = line[tail_start:end]
        ow = OTHER_WORK_RE.search(tail)
        if ow:
            tail = tail[:ow.start()]
            end = tail_start + ow.start()
        c = Citation(book, start)
        if SOURCES[book]["kind"] == "hadith":
            hm = _T_HADITH.match(tail)
            if hm:
                c.numbers = [int(x) for x in re.findall(r"\d+", hm.group(1))]
                c.end = end + (1 if end < len(line) and line[end] == ")" and "(" in line[start:tail_start + 1] else 0)
                c.text = line[c.start:c.end]
                cites.append(c)
            continue
        vol = None
        pos, last_was_page = 0, False
        while pos < len(tail):
            for rx, kind in ((_T_VP, "vp"), (_T_VOL, "vol"), (_T_PP, "pp"), (_T_NO, "no"),
                             (_T_NOTE, "note"), (_T_CONT, "cont")):
                m = rx.match(tail, pos)
                if not m:
                    continue
                if kind == "vp":
                    vol = int(m.group(1)); a = int(m.group(2)); b = int(m.group(3) or a)
                    c.refs.append((vol, a, max(a, b))); last_was_page = True
                elif kind == "vol":
                    vol = int(m.group(1)); last_was_page = False
                elif kind == "pp":
                    if vol is None:          # "pp." with no volume known: not resolvable, skip it
                        pos = m.end()
                        break
                    for piece in re.split(r"\s*,\s*", m.group(1)):
                        ab = re.split(r"\s*[–-]\s*", piece)
                        a = int(ab[0]); b = int(ab[-1])
                        c.refs.append((vol, a, max(a, b)))
                    last_was_page = True
                elif kind == "no":
                    c.entries.append(int(m.group(1))); last_was_page = False
                elif kind == "note":
                    c.tahqiq = True
                elif kind == "cont":
                    if not (last_was_page and vol is not None):
                        pos += 1             # a bare ", N" not following a page: not a citation
                        break
                    a = int(m.group(1)); b = int(m.group(2) or a)
                    c.refs.append((vol, a, max(a, b)))
                pos = m.end()
                break
            else:
                pos += 1
                continue
        if c.refs or c.entries:
            # include a closing ")" in the span if the citation opened one
            c.end = end + (1 if end < len(line) and line[end] == ")" and "(" in line[start:tail_start + 1] else 0)
            c.text = line[c.start:c.end]
            cites.append(c)
    return cites


# ════════════════════════════════════════════════════════════════════════════
#  Notes
# ════════════════════════════════════════════════════════════════════════════

def parse_frontmatter(content):
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return None, content
    data, cur = {}, None
    for line in fm_match.group(1).splitlines():
        lm = re.match(r"^\s*-\s+(.+)$", line)
        if lm and cur:
            data.setdefault(cur, []).append(lm.group(1).strip().strip("\"'"))
            continue
        kv = re.match(r"^([a-zA-Z0-9_]+):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            if not val:
                cur = key; data[key] = []
            else:
                cur = None
                if val.startswith("[") and val.endswith("]"):
                    data[key] = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
                else:
                    data[key] = val.strip("\"'")
        else:
            cur = None
    return data, content[fm_match.end():]


def load_notes():
    notes, aliases = {}, {}
    for fpath in sorted(glob.glob(os.path.join(VAULT_DIR, "*.md"))):
        if os.path.basename(fpath) in NON_NOTES:
            continue
        b = os.path.splitext(os.path.basename(fpath))[0]
        with open(fpath, encoding="utf-8") as f:
            raw = f.read()
        fm, body = parse_frontmatter(raw)
        notes[b] = {"path": fpath, "fm": fm or {}, "body": body, "raw": raw}
        aliases[b] = b
        al = (fm or {}).get("aliases", [])
        for a in (al if isinstance(al, list) else [al]):
            if a:
                aliases[a.strip()] = b
    return notes, aliases


# ── names, slugs and alias collisions (shared with site_search.py) ─────────────────────────────

def slugify(name):
    """The URL slug Quartz gives a title or an alias — a Python copy of slugifyPath/slugifyAlias
    in patch-quartz.mjs. Keep the two in step."""
    import unicodedata
    s = unicodedata.normalize("NFD", name)
    s = re.sub(r"[\u0300-\u036f]", "", s)
    s = re.sub(r"[ʿʻʾʽ`\u02BF\u02BE\u2018\u2019]", "", s)
    s = re.sub(r"[\u0600-\u06FF]", "", s)
    parts = []
    for seg in s.split("/"):
        seg = re.sub(r"\s+", "-", seg).replace("&", "-and-").replace("%", "-percent")
        seg = re.sub(r'[?#<>:"|*]', "", seg)
        parts.append(seg.lower())
    return re.sub(r"/$", "", "/".join(parts))


def load_search_config():
    """site_search.json: {"extra": {note: [names]}, "primary": {name: note}, "ambiguous": [names],
    "expect": {query: note}}. A missing file is an empty configuration."""
    cfg = {"extra": {}, "primary": {}, "ambiguous": [], "expect": {}}
    if os.path.exists(SEARCH_CFG):
        with open(SEARCH_CFG, encoding="utf-8") as f:
            cfg.update({k: v for k, v in json.load(f).items() if k in cfg})
    return cfg


def note_aliases(note):
    al = note["fm"].get("aliases", [])
    return [a.strip() for a in (al if isinstance(al, list) else [al]) if a and a.strip()]


def name_claims(notes, cfg):
    """slug → {note: the name as written}, for every alias and every extra search name. A slug with
    no Latin letter or digit (an Arabic-script alias) makes no usable URL and is left out."""
    claims = defaultdict(dict)
    for b, n in notes.items():
        for name in note_aliases(n) + list(cfg["extra"].get(b, [])):
            sl = slugify(name)
            if re.search(r"[a-z0-9]", sl) and "/" not in sl and sl != slugify(b):
                claims[sl].setdefault(b, name)
    return claims


def alias_report(notes, cfg):
    """(collisions, errors). A collision is a name claimed by several notes, or by a note other than
    the one whose title it is, that site_search.json does not settle. Errors are mistakes in
    site_search.json itself (a note that does not exist, a ruling that names a non-claimant)."""
    title_slug = {slugify(b): b for b in notes}
    claims = name_claims(notes, cfg)
    primary = {slugify(k): v for k, v in cfg["primary"].items()}
    ambiguous = {slugify(k) for k in cfg["ambiguous"]}
    collisions, errors = [], []
    for sl, owners in sorted(claims.items()):
        if sl in title_slug:
            collisions.append((sl, f"is the title of [[{title_slug[sl]}]] but also a name of "
                               + ", ".join(f"[[{o}]]" for o in owners)))
        elif len(owners) > 1 and sl not in ambiguous and primary.get(sl) not in owners:
            collisions.append((sl, f"“{next(iter(owners.values()))}” is claimed by "
                               + ", ".join(f"[[{o}]]" for o in sorted(owners))))
    for key in ("extra",):
        for b in cfg[key]:
            if b not in notes:
                errors.append(f'"{key}" names a note that does not exist: {b!r}')
    for name, b in cfg["primary"].items():
        if b not in notes:
            errors.append(f'"primary" sends {name!r} to a note that does not exist: {b!r}')
        elif b not in claims.get(slugify(name), {}):
            errors.append(f'"primary" sends {name!r} to [[{b}]], which has no such alias or extra name')
    for q, b in cfg["expect"].items():
        if b not in notes:
            errors.append(f'"expect" maps {q!r} to a note that does not exist: {b!r}')
    return collisions, errors


def build_name_words(notes, aliases):
    """Capitalised words from titles/aliases that never occur lower-case in prose: proper names."""
    lower_seen = set()
    for n in notes.values():
        lower_seen.update(re.findall(r"\b[a-z][a-zāīūḥṣḍṭẓ]+\b", n["body"]))
    words = set()
    for name in aliases:
        if any(w.lower() in EN_STOP for w in re.findall(r"[A-Za-z]+", name)):
            continue                              # an English alias ("The Cow", "Battle of Badr")
        for t in re.findall(r"[A-Za-zĀ-ſḀ-ỿʿʾʻ’'.\-]+", name):
            low = t.lower().strip(".")
            if t[:1].isupper() and low not in lower_seen and low not in EN_STOP and len(low) > 2:
                words.add(low)
    return words


def plain(text):
    """Strip markdown, keep wikilink display text."""
    t = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    t = re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)
    t = re.sub(r"\$\$.*?\$\$", " ", t)
    return t


# ════════════════════════════════════════════════════════════════════════════
#  Content triage
# ════════════════════════════════════════════════════════════════════════════

class Finding:
    __slots__ = ("note", "line", "kind", "detail", "claim", "cites", "hint")

    def __init__(self, note, line, kind, detail, claim="", cites="", hint=""):
        self.note, self.line, self.kind, self.detail = note, line, kind, detail
        self.claim, self.cites, self.hint = claim, cites, hint

    def fmt(self):
        s = f"  L{self.line:<4} [{self.kind}] {self.detail}"
        if self.cites:
            s += f"  ← {self.cites}"
        if self.hint:
            s += f"  ({self.hint})"
        if self.claim:
            c = re.sub(r"\s+", " ", self.claim).strip()
            s += f"\n          “{c[:160]}{'…' if len(c) > 160 else ''}”"
        return s


def _term_phrases(text, name_words):
    """Runs of transliterated words; italic Arabic phrases separately."""
    phrases = []
    for m in re.finditer(r"(?<![*\w])\*([^*\n]{2,80})\*(?!\*)", text):
        inner = m.group(1)
        words = re.findall(r"[\w’'ʿʾʻ.\-]+", inner)
        if len(words) == 1 and not words[0][:1].isupper():
            continue                      # a one-word Arabic gloss of an English term: not a source claim
        def arabic_word(w):
            lw = w.lower()
            return (any(c in _DIACRITICS for c in w) or re.match(r"^(?:wa|bi|li|fa)?-?a?l?-", lw)
                    or (len(lw) <= 5 and lw.isalpha() and lw not in EN_STOP))
        if (any(c in _DIACRITICS for c in inner) and not any(w.lower() in EN_STOP for w in words)
                and all(arabic_word(w) for w in words)):
            phrases.append(("italic", words))
    t = re.sub(r"(?<![*\w])\*([^*\n]{2,80})\*(?!\*)", " ", text)
    t = re.sub(r"[*_]", "", plain(t))
    run = []
    for tok in re.findall(r"[A-Za-zĀ-ſḀ-ỿʿʾʻ’'.\-]+|[^\sA-Za-zĀ-ſḀ-ỿʿʾʻ’'.\-]+", t):
        low = tok.lower().strip(".,;:")
        if is_arabicish(tok, name_words) or (run and low in WEAK):
            run.append(tok)
        elif tok.strip() == "":
            continue
        else:
            if run:
                phrases.append(("name", run))
            run = []
    if run:
        phrases.append(("name", run))
    return phrases


class Auditor:
    def __init__(self, indices, notes, aliases):
        self.corp = make_corpora(indices)
        self.notes = notes
        self.name_words = build_name_words(notes, aliases)
        self._rx_cache = {}

    def _rx(self, word, vocalized=False):
        key = (word, vocalized)
        if key not in self._rx_cache:
            r = translit_regex(word, vocalized)
            self._rx_cache[key] = re.compile(r) if r else None
        return self._rx_cache[key]

    def _pool(self, cites):
        pool = []
        for c in cites:
            for v, p in c.pages():
                n = self.corp[c.book].norm(v, p)
                if n:
                    pool.append((c.book, v, p, n))
        return pool

    def _near(self, cites, test):
        """Look a few pages either side of each citation for something test() accepts."""
        for c in cites:
            for v, a, b in c.refs:
                if b - a > BROAD_RANGE:
                    continue
                for p in list(range(a - NEAR, a)) + list(range(b + 1, b + NEAR + 1)):
                    n = self.corp[c.book].norm(v, p)
                    if n and test(n):
                        return f"found at {BOOK_LABEL[c.book]} {v}:{p}"
        return ""

    def check_claim(self, note, lineno, claim, cites, out):
        pool = self._pool(cites)
        if not pool:
            return
        label = "; ".join(c.label() for c in cites)
        tahqiq_cited = any(c.tahqiq for c in cites)
        for c in cites:
            if c.book == "B" and any((v, a) < BIDAYAH_FROM for v, a, _ in c.refs):
                out.append(Finding(note, lineno, "scope", "al-Bidāyah cited for the period before the Prophet's ﷺ "
                                   "death; use Subul al-Hudā, al-Iṣābah or the Ṣaḥīḥayn there", claim, label))
        # numbers
        page_nums = set().union(*(n["nums"] for *_, n in pool))
        for num in sorted(english_numbers(plain(claim))):
            if num not in page_nums:
                hint = self._near(cites, lambda n, num=num: num in n["nums"])
                out.append(Finding(note, lineno, "number", str(num), claim, label, hint))
        # transliterated terms
        reported = set()
        for kind, words in _term_phrases(claim, self.name_words):
            checks = []
            for w in words:
                low = w.lower().strip(".,;:")
                if low in WEAK or low in TOLERATED:
                    continue
                rx = self._rx(w, vocalized=(kind == "italic"))
                if rx:
                    checks.append((w, rx))
            if not checks:
                continue
            missing, only_tahqiq = [], []
            for w, rx in checks:
                in_matn = any(rx.search(n["matn"]) for *_, n in pool)
                in_tq = any(rx.search(n["tahqiq"]) for *_, n in pool)
                if not in_matn and not in_tq:
                    missing.append((w, rx))
                elif not in_matn and in_tq and not tahqiq_cited:
                    only_tahqiq.append(w)
            phrase = " ".join(words)
            missing = [(w, rx) for w, rx in missing if w.lower() not in reported]
            # "X b. Y": the page often gives only the ism. Stay strict for nasab chains (2+ b./bint),
            # otherwise accept the name when its first distinctive word is on the page.
            links = sum(1 for w in words if w.lower().strip(".") in ("b", "bint", "ibn"))
            if kind == "name" and links < 2 and len(checks) > 1 and missing and checks[0] not in missing:
                missing = []
            if missing:
                reported.update(w.lower() for w, _ in missing)
                hint = self._near(cites, lambda n, ms=missing: all(rx.search(n["matn"] + n["tahqiq"]) for _, rx in ms))
                miss = ", ".join(w for w, _ in missing)
                detail = f"{phrase}" if len(checks) == 1 else f"{phrase}  [missing: {miss}]"
                out.append(Finding(note, lineno, "term" if kind == "name" else "phrase", detail, claim, label, hint))
            elif only_tahqiq and len(only_tahqiq) == len(checks):
                out.append(Finding(note, lineno, "apparatus", phrase, claim, label,
                                   "occurs only in the editors' footnotes; cite as n. X (taḥqīq)"))

    def check_quote(self, note, lineno, quote, cites, out):
        pool = self._pool(cites)
        if not pool:
            return
        q = ar_skeleton(quote)
        if len(q) < 8:
            return
        hay = "".join(n["matn"] + n["tahqiq"] for *_, n in pool)
        if q in hay:
            return
        qw = [w for w in ar_words(quote) if len(w) >= 3]
        page_words = set()
        for *_, n in pool:
            page_words.update(n["matn_words"]); page_words.update(n["tahqiq_words"])
        if qw:
            ratio = sum(1 for w in qw if w in page_words) / len(qw)
            if ratio >= 0.85:
                return
        else:
            ratio = 0
        hint = self._near(cites, lambda n: q in n["matn"] + n["tahqiq"])
        out.append(Finding(note, lineno, "quote", f"«{quote.strip()[:70]}» — {int(ratio * 100)}% of words on page",
                           "", "; ".join(c.label() for c in cites), hint))

    def audit_note(self, bname):
        note = self.notes[bname]
        out = []
        lines = expand_footnotes(note["raw"])
        in_fm = lines[0].strip() == "---"
        in_refs = False
        pending_quotes = []          # (lineno, quote) waiting for a citation on a following line
        for i, line in enumerate(lines, 1):
            if i > 1 and in_fm and line.strip() == "---":
                in_fm = False
                continue
            if in_fm and not ANCHOR_RE.search(line):
                continue
            if in_fm and re.match(r"^\s*primary_source:", line):
                continue
            if re.match(r"^#{1,6}\s", line):
                in_refs = bool(re.search(r"references|bibliograph|sources", line, re.I))
                pending_quotes = []
                continue
            stripped = line.strip()
            if not stripped:
                pending_quotes = []
                continue
            cites = parse_citations(line)
            # other works cited as sources
            if in_refs:
                if (stripped[:1].isdigit() or stripped.startswith(("-", "*"))) and not ANCHOR_RE.search(line):
                    # a sub-item giving pages ("- Vol. 1, pp. 455–456, entry no. 736") continues its parent
                    titled = re.search(r"\*[^*]{3,}\*", line) and not re.search(r"\b(?:vol|entry)\b", line, re.I)
                    if OTHER_WORK_RE.search(line) or titled:
                        out.append(Finding(bname, i, "other-work", "References entry outside the two canonical books",
                                           stripped))
                continue
            for pm in re.finditer(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)", line):
                inner = pm.group(1)
                om = OTHER_WORK_RE.search(inner)
                if om and not om.group(0).startswith(("Qur", "Q.", "Sūra")) and len(inner) < 220:
                    framed = re.search(r"apud|as cited|cited (?:by|in)|quoted (?:by|in)|via|transmitted", inner, re.I)
                    if not framed:
                        kind = "cited alongside" if ANCHOR_RE.search(inner) else "cited directly"
                        out.append(Finding(bname, i, "other-work", f"{om.group(0)} {kind}", inner))
            # Arabic quotations
            quotes = re.findall(r"«([^»]+)»", line)
            if quotes and "$$" not in line:
                if cites:
                    for q in quotes:
                        self.check_quote(bname, i, q, cites, out)
                else:
                    pending_quotes.extend((i, q) for q in quotes)
            if cites and pending_quotes:
                for qi, q in pending_quotes:
                    self.check_quote(bname, qi, q, cites, out)
                pending_quotes = []
            # claims
            if not cites:
                body = plain(re.sub(r"«[^»]*»", "", line))
                body = re.sub(r"^[>\s\-*\d.|]+", "", body)
                if (len(re.findall(r"[A-Za-z]", body)) > 90 and not stripped.startswith(("> [!", "|", "$$"))
                        and not re.match(r"^\|?\s*-{3,}", stripped) and not in_fm):
                    out.append(Finding(bname, i, "uncited", "substantive line with no citation to either book", body))
                continue
            # group citations separated only by punctuation into one claim
            groups, cur = [], [cites[0]]
            for c in cites[1:]:
                if re.fullmatch(r"[\s;,.*()\[\]]*", line[cur[-1].end:c.start]):
                    cur.append(c)
                else:
                    groups.append(cur); cur = [c]
            groups.append(cur)
            prev = 0
            for g in groups:
                claim = line[prev:g[0].start]
                if in_fm:
                    claim = re.sub(r"^\s*[\w_]+:\s*", "", claim)
                if any(c.broad() for c in g) and not any(c.pages() for c in g):
                    prev = g[-1].end
                    continue
                if re.search(r"[A-Za-z0-9]", claim):
                    self.check_claim(bname, i, claim, g, out)
                prev = g[-1].end
            trailing = plain(line[prev:])
            if len(re.findall(r"[A-Za-z]", trailing)) > 90 and not in_fm:
                out.append(Finding(bname, i, "uncited", "text after the last citation on this line", trailing))
        return out


# ════════════════════════════════════════════════════════════════════════════
#  Source sheets
# ════════════════════════════════════════════════════════════════════════════

FOOTDEF_RE = re.compile(r"^\[\^([^\]]+)\]:\s?(.*)$")
FOOTREF_RE = re.compile(r"\[\^([^\]]+)\](?!:)")


def expand_footnotes(raw):
    """Lines of a note with each footnote reference replaced by "(definition)", and the definition
    lines themselves blanked — so a claim is checked against the pages its footnote cites."""
    lines = raw.split("\n")
    defs = {}
    for l in lines:
        m = FOOTDEF_RE.match(l)
        if m:
            defs[m.group(1)] = m.group(2).strip().replace('"', "'")   # a quote would end the citation span
    if not defs:
        return lines
    out = []
    for l in lines:
        if FOOTDEF_RE.match(l):
            out.append("")
            continue
        out.append(FOOTREF_RE.sub(lambda m: f" ({defs[m.group(1)]})" if m.group(1) in defs else m.group(0), l))
    return out


QUESTIONS_PATH = os.path.join(VAULT_DIR, "ledger", "QUESTIONS.md")


def load_questions():
    """{section name: [question blocks]} from ledger/QUESTIONS.md — a block is a '- [ ]' / '- [x]' item
    with its indented continuation lines."""
    out, sec = {}, None
    if not os.path.exists(QUESTIONS_PATH):
        return out
    for line in open(QUESTIONS_PATH, encoding="utf-8").read().split("\n"):
        if line.startswith("## "):
            sec = line[3:].strip()
            out[sec] = []
        elif sec and re.match(r"- \[[ xX]\] ", line):
            out[sec].append(line)
        elif sec and out[sec] and line.startswith("  ") and line.strip():
            out[sec][-1] += "\n" + line
    return out


def print_questions(notes):
    qs = load_questions()
    is_open = lambda q: q.startswith("- [ ]")
    total = 0
    for sec, items in qs.items():
        n = sum(map(is_open, items))
        if not n:
            continue
        total += n
        missing = "" if sec == "General" or sec in notes else "   (no note of this name)"
        print(f"{n:3d} open   {sec}{missing}")
    print(f"\n{total} open question(s) in ledger/QUESTIONS.md. "
          "See one note's with:  python3 audit.py --sheet \"<note>\"")
    return 0


def write_sheet(auditor, bname, findings):
    note = auditor.notes[bname]
    os.makedirs(REVIEW_DIR, exist_ok=True)
    path = os.path.join(REVIEW_DIR, f"{bname}.sheet.md")
    by_line = defaultdict(list)
    for f in findings:
        by_line[f.line].append(f)
    cited = []
    seen = set()
    out = [f"# Source sheet — {bname}", "",
           "Generated by `audit.py --sheet`. Left: each cited line of the note with the audit's flags.",
           "Below: the full text of every page the note cites, matn and taḥqīq separated. A flag is a",
           "prompt to look, not a verdict; an unflagged line is not thereby verified.", "",
           ]
    qs = load_questions()
    mine = [q for q in qs.get(bname, []) if q.startswith("- [ ]")]
    if mine:
        out += ["## Open questions for you", "",
                "From `ledger/QUESTIONS.md` — rule on them there (`- [x]` and the ruling after `→`).", ""]
        out += mine
        general = [q for q in qs.get("General", []) if q.startswith("- [ ]")]
        if general and any("See General" in q for q in mine):
            out += ["", "General questions these refer to:", ""] + general
        out.append("")
    out += ["## Claims", ""]
    for i, line in enumerate(expand_footnotes(note["raw"]), 1):
        cites = parse_citations(line)
        if not cites and i not in by_line:
            continue
        txt = re.sub(r"\s+", " ", plain(line)).strip()
        out.append(f"**L{i}** — {txt}")
        labels = []
        for c in cites:
            if c.label() not in labels:
                labels.append(c.label())
        if labels:
            out.append("- cites: " + "; ".join(labels))
        for c in cites:
            for v, p in c.pages():
                if (c.book, v, p) not in seen:
                    seen.add((c.book, v, p)); cited.append((c.book, v, p))
            if c.broad():
                out.append("  - (range too broad for automatic checking)")
        for f in by_line.get(i, []):
            out.append(f"- ⚠ **{f.kind}**: {f.detail}" + (f" — {f.hint}" if f.hint else ""))
        out.append("")
    out += ["## Cited pages", ""]
    for book, v, p in sorted(cited):
        r = auditor.corp[book].raw(v, p)
        out.append(f"### {BOOK_LABEL[book]} {v}:{p}")
        if r is None:
            out += ["", "*Page not present in the EPUB.*", ""]
            continue
        out += ["", '<div dir="rtl">', "", r[0].replace("\n", "\n\n"), "", "</div>", ""]
        if r[1]:
            out += ["**Taḥqīq (editors' apparatus)**", "", '<div dir="rtl">', "",
                    r[1].replace("\n", "\n\n"), "", "</div>", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return path


# ════════════════════════════════════════════════════════════════════════════
#  Main
# ════════════════════════════════════════════════════════════════════════════

def resolve_note(notes, name):
    if name in notes:
        return name
    name = name[:-3] if name.endswith(".md") else name
    if name in notes:
        return name
    hits = [n for n in notes if name.lower() in n.lower()]
    if len(hits) == 1:
        return hits[0]
    close = difflib.get_close_matches(name, list(notes), n=5, cutoff=0.5)
    sys.exit(f"No unique note matches {name!r}." + (f" Candidates: {hits[:8] or close}" if hits or close else ""))


_AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
_REPORT_START = {
    "K": lambda n: re.compile(r"(?:^|\n)\s*" + n + r"\s*-"),
    "M": lambda n: re.compile(r"(?:^|\n|\s)(?:[٠-٩]+\s*-\s*)?(?:م-?\s*)?\(" + n + r"\)"),
}
_NEXT_REPORT = {
    "K": re.compile(r"\n\s*([٠-٩]+)\s*-"),
    "M": re.compile(r"(?:^|\n|\s)[٠-٩]+\s*-\s*(?:م-?\s*)?\(([٠-٩]+)\)"),
}


def extract_report(book, number, text):
    """The text of one ḥadīth cut out of the pages it is on — for Muslim, every sub-report carrying the
    same bracketed number, joined with "…" where other reports come between them — or None."""
    n = str(number).translate(_AR_DIGITS)
    segments, pos = [], 0
    start_re = _REPORT_START[book](n)
    while True:
        m = start_re.search(text, pos)
        if not m:
            break
        rest = text[m.start():].lstrip("\n")
        end = len(rest)
        for nx in _NEXT_REPORT[book].finditer(rest, 1):
            if nx.group(1) != n:
                end = nx.start()
                break
        seg = rest[:end]
        lines = seg.rstrip().split("\n")
        while len(lines) > 1 and re.match(r"\s*(?:[٠-٩]+\s*-\s*)?(?:باب|كتاب)",
                                          re.sub(r"[\u064B-\u0652\u0670]", "", lines[-1])):
            lines.pop()                               # a chapter heading belonging to the next report
        segments.append("\n".join(lines).strip())
        pos = m.start() + len(text[m.start():]) - len(rest) + max(end, 1)
        if book == "K":
            break
    return "\n…\n".join(segments) if segments else None


_AR_LETTERS_ONLY = re.compile(r"[^\u0621-\u063A\u0641-\u064A]")
_LEDGER_ID = re.compile(r"^### ([SIBKM])(\d+)(?:\.(\d+))?\.(\d+) · (matn|taḥqīq) · (\S+)\s*$")
LEDGER_KINDS = {"plain", "qīla", "khilāf", "verdict", "hedge", "via", "gloss"}


def check_ledgers(corpora):
    """Every Arabic snippet in ledger/*.md must be verbatim on the page its id names (letters only:
    vocalisation, punctuation and spacing are ignored; a run-over onto the next page is allowed).
    Returns (entries checked, [problems])."""
    letters = lambda t: _AR_LETTERS_ONLY.sub("", _TASHKIL.sub("", t))
    n, bad = 0, []
    for fpath in sorted(glob.glob(os.path.join(VAULT_DIR, "ledger", "*.md"))):
        fname = os.path.basename(fpath)
        if fname == "README.md":
            continue
        lines = open(fpath, encoding="utf-8").read().split("\n")
        for i, line in enumerate(lines):
            if not line.startswith("### "):
                continue
            m = _LEDGER_ID.match(line)
            where = f"{fname}:{i + 1}"
            if not m:
                bad.append(f"{where}  heading not in the form '### S4.174.07 · matn · plain'")
                continue
            book, a, b, _, tier, kind = m.groups()
            n += 1
            if kind not in LEDGER_KINDS:
                bad.append(f"{where}  unknown kind {kind!r}")
            j, quoted = i + 1, []
            while j < len(lines) and lines[j].startswith(">"):
                quoted.append(lines[j][1:].strip())
                j += 1
            snippet = " ".join(quoted)
            if not snippet:
                bad.append(f"{where}  no Arabic snippet")
                continue
            corp = corpora[book]
            if SOURCES[book]["kind"] == "hadith":
                keys = corp.hadith.get(str(int(a))) or []
                pages = [tuple(map(int, k.split(":"))) for k in keys]
            else:
                pages = [(int(a), int(b or 0)), (int(a), int(b or 0) + 1)]
            raws = [corp.raw(v, p) for v, p in pages]
            if not raws or raws[0] is None:
                bad.append(f"{where}  {line[4:].split(' ')[0]}: page or report not in the EPUB")
                continue
            if SOURCES[book]["kind"] == "hadith":       # the Ṣaḥīḥayn EPUBs do not mark editors' notes apart
                text = letters("\n".join(r[0] + "\n" + r[1] for r in raws if r))
            else:
                text = letters("\n".join(r[0 if tier == "matn" else 1] for r in raws if r))
            pos = 0
            for seg in snippet.split("…"):
                seg = letters(seg)
                if not seg:
                    continue
                at = text.find(seg, pos)
                if at < 0:
                    bad.append(f"{where}  {line[4:].split(' ')[0]}: not verbatim in the {tier} — «{seg[:40]}…»")
                    break
                pos = at + len(seg)
    return n, bad


def print_pages(args):
    # Vocalisation marks are dropped unless --tashkil is given: they cost a reader-model about a quarter
    # of the Ṣaḥīḥayn's text and carry nothing a claim rests on. Use --tashkil to copy a «…» quotation.
    out = open(args.out, "w", encoding="utf-8") if args.out else None

    def print(*a, **k):                                       # noqa: A001 — local shadow, this function only
        if not args.tashkil:
            a = tuple(_TASHKIL.sub("", x) if isinstance(x, str) else x for x in a)
        builtins.print(*a, **({**k, "file": out} if out else k))
    corpora = make_corpora(load_or_build_indices(force=args.reindex))
    book = args.page[0].upper()[:1]
    if book not in SOURCES:
        sys.exit("--page takes S (Subul al-Hudā), I (al-Iṣābah), B (al-Bidāyah) then vol:page[-page] …, "
                 "or K (al-Bukhārī) / M (Muslim) then ḥadīth numbers")
    corp = corpora[book]
    for ref in args.page[1:]:
        if SOURCES[book]["kind"] == "hadith":
            keys = corp.hadith.get(str(int(ref))) if ref.isdigit() else None
            if not keys:
                print(f"══════ {BOOK_LABEL[book]} no. {ref}: not found ══════\n")
                continue
            pages = [tuple(map(int, k.split(":"))) for k in keys]
            text = "\n".join((corp.raw(v, p) or ("", ""))[0] for v, p in pages)
            report = extract_report(book, int(ref), text)
            if report and not args.whole_pages:
                print(f"══════ {BOOK_LABEL[book]} no. {ref} — {', '.join(keys)} ══════")
                print(report + "\n")
                continue
            print(f"══════ {BOOK_LABEL[book]} no. {ref} — on {', '.join(keys)} (other reports may share these pages) ══════")
        else:
            m = re.fullmatch(r"(\d+):(\d+)(?:[-–](\d+))?", ref)
            if not m:
                sys.exit(f"Bad page reference {ref!r}; use vol:page or vol:page-page")
            v, a = int(m.group(1)), int(m.group(2))
            pages = [(v, p) for p in range(a, int(m.group(3) or a) + 1)]
        for v, p in pages:
            r = corp.raw(v, p)
            print(f"══════ {BOOK_LABEL[book]} {v}:{p} ══════")
            if r is None:
                print("(page not present in the EPUB)\n")
                continue
            print("── matn ──\n" + r[0])
            if r[1]:
                print("── taḥqīq (editors' apparatus) ──\n" + r[1])
            print()
    if out:
        out.close()
        builtins.print(f"wrote {args.out} ({sum(1 for _ in open(args.out, encoding='utf-8'))} lines)")
    return 0


def run(args):
    if args.page:
        return print_pages(args)
    if args.exists:
        _, aliases = load_notes()
        for name in args.exists:
            target = aliases.get(name)
            print(("OK  " if target else "--  ") + name + (f"   → [[{target}|{name}]]" if target and target != name else ""))
        return 0
    if args.questions:
        return print_questions(load_notes()[0])
    if args.ledger:
        n, bad = check_ledgers(make_corpora(load_or_build_indices(force=args.reindex)))
        for line in bad:
            print("  " + line)
        print(f"Ledger snippets: {n} checked, {len(bad)} problem(s)")
        return 1 if bad else 0
    print("=== Nabiwiki Knowledge Graph & Citation Audit ===\n")
    indices = load_or_build_indices(force=args.reindex)
    notes, aliases = load_notes()
    auditor = Auditor(indices, notes, aliases)

    only = resolve_note(notes, args.note or args.sheet) if (args.note or args.sheet) else None

    # ── structural ────────────────────────────────────────────────────────
    hub_orphans = []
    hub = notes.get("The Sīrah")
    if hub:
        hub_links = set(re.findall(r"\[\[([^\|\]#]+)(?:#[^\|\]]+)?(?:\|[^\]]+)?\]\]", hub["raw"]))
        hub_orphans = [b for b in notes if b != "The Sīrah" and b not in hub_links]

    total_links, unresolved, multiline = 0, defaultdict(list), []
    cite_total = Counter()
    out_of_bounds = []
    missing_fm, missing_fields, missing_ps = [], [], []
    for b, n in notes.items():
        raw = n["raw"]
        for bad in re.findall(r"\[\[[^\]]*\n[^\]]*\]\]", raw):
            multiline.append((b, bad.replace("\n", "\\n")))
        for t in re.findall(r"\[\[([^\|\]#\n]+)(?:#[^\|\]]+)?(?:\|[^\]]+)?\]\]", raw):
            total_links += 1
            if t.strip() not in aliases:
                unresolved[t.strip()].append(b)
        for ln, line in enumerate(raw.split("\n"), 1):
            for c in parse_citations(line):
                for hn in c.numbers:
                    cite_total[c.book] += 1
                    if str(hn) not in auditor.corp[c.book].hadith:
                        out_of_bounds.append((b, ln, f"{BOOK_LABEL[c.book]} no. {hn}", c.text.strip()))
                for v, a, bb in c.refs:
                    cite_total[c.book] += 1
                    for p in sorted({a, bb}):
                        if not auditor.corp[c.book].has(v, p):
                            out_of_bounds.append((b, ln, f"{BOOK_LABEL[c.book]} {v}:{p}", c.text.strip()))
        fm = n["fm"]
        if not fm:
            missing_fm.append(b); continue
        for req in ("title", "arabic", "type", "tags"):
            if req not in fm:
                missing_fields.append((b, req))
        if fm.get("type") not in ("index", "source") and "primary_source" not in fm:
            missing_ps.append(b)

    alias_collisions, search_cfg_errors = alias_report(notes, load_search_config())

    # ── content triage ───────────────────────────────────────────────────
    findings = {}
    if not args.no_content:
        targets = [only] if only else list(notes)
        for k, b in enumerate(targets):
            findings[b] = auditor.audit_note(b)
            if not only and sys.stderr.isatty():
                print(f"\r  content triage {k + 1}/{len(targets)}", end="", file=sys.stderr)
        if not only and sys.stderr.isatty():
            print("\r" + " " * 40 + "\r", end="", file=sys.stderr)

    kinds = Counter(f.kind for fs in findings.values() for f in fs)

    # ── report ───────────────────────────────────────────────────────────
    print(f"Content notes: {len(notes)}   sources: " + ", ".join(
        f"{BOOK_LABEL[k]} ({len(c.hadith) or len(c.pages)} {'ḥadīths' if c.hadith else 'pages'})"
        for k, c in auditor.corp.items()) + "\n")
    print("-" * 64)
    print("STRUCTURE")
    print(f"  Hub completeness       {'PASS' if not hub_orphans else f'FAIL ({len(hub_orphans)} orphans)'}")
    print(f"  Wrapped links          {'PASS' if not multiline else f'FAIL ({len(multiline)})'}")
    print(f"  Citation bounds        " + ", ".join(f"{BOOK_LABEL[k]} {cite_total[k]}" for k in SOURCES)
          + f" refs; out of bounds {len(out_of_bounds)}")
    print(f"  Wikilinks              {total_links} total, {len(unresolved)} unresolved targets (by design)")
    print(f"  Frontmatter            missing FM {len(missing_fm)}, missing fields {len(missing_fields)}, "
          f"missing primary_source {len(missing_ps)}")
    alias_bad = len(alias_collisions) + len(search_cfg_errors)
    print(f"  Alias collisions       {'PASS' if not alias_bad else f'FAIL ({len(alias_collisions)} unsettled, {len(search_cfg_errors)} errors in site_search.json)'}")
    if findings:
        print("CONTENT TRIAGE  (prompts for a human reader, not verdicts)")
        for k in ("number", "term", "phrase", "quote", "apparatus", "uncited", "other-work", "scope"):
            print(f"  {k:<11} {kinds.get(k, 0)}")
        hinted = sum(1 for fs in findings.values() for f in fs if f.hint.startswith("found at"))
        print(f"  …of which the missing item occurs within {NEAR} pages of the citation: {hinted}")
    print("-" * 64 + "\n")

    if hub_orphans:
        print(f"Orphaned notes not linked from The Sīrah.md ({len(hub_orphans)}):")
        for o in sorted(hub_orphans):
            print(f"  - [[{o}]]")
        print()
    if multiline:
        print(f"Wrapped links ({len(multiline)}):")
        for b, s in multiline:
            print(f"  - {b}: {s}")
        print()
    if out_of_bounds:
        print(f"Out-of-bounds citations ({len(out_of_bounds)}):")
        for b, ln, key, txt in (out_of_bounds if args.citations else out_of_bounds[:15]):
            print(f"  - {b} L{ln}: {key} not in EPUB   [{txt[:70]}]")
        if len(out_of_bounds) > 15 and not args.citations:
            print(f"  … {len(out_of_bounds) - 15} more (--citations for all)")
        print()
    if alias_collisions or search_cfg_errors:
        print(f"Alias collisions ({len(alias_collisions)}) — give the name to one note, or settle it in "
              f"site_search.json (\"primary\": one note owns the redirect; \"ambiguous\": a disambiguation page):")
        for sl, msg in alias_collisions:
            print(f"  - /{sl}: {msg}")
        for e in search_cfg_errors:
            print(f"  - site_search.json: {e}")
        print()
    if missing_fields or missing_ps:
        for b, f in missing_fields[:10]:
            print(f"  missing {f}: {b}")
        for b in missing_ps[:10]:
            print(f"  missing primary_source: {b}")
        print()
    if args.links:
        pool = list(notes) + list(aliases)
        print(f"Unresolved wikilink targets ({len(unresolved)}):")
        for t, src in sorted(unresolved.items(), key=lambda x: -len(x[1])):
            close = difflib.get_close_matches(t, pool, n=2, cutoff=0.7)
            print(f"  - [[{t}]] ×{len(src)} ({', '.join(src[:2])}{'…' if len(src) > 2 else ''})"
                  + (f" → did you mean {close}?" if close else ""))
        print()

    if findings:
        if only or args.content:
            for b in ([only] if only else sorted(findings, key=lambda x: -len(findings[x]))):
                fs = findings[b]
                if not fs:
                    continue
                print(f"── {b} ({len(fs)} findings)")
                for f in fs:
                    print(f.fmt())
                print()
        else:
            ranked = sorted(findings.items(), key=lambda x: -len(x[1]))[:15]
            print("Notes with the most content findings (use --note NAME for detail):")
            for b, fs in ranked:
                c = Counter(f.kind for f in fs)
                print(f"  {len(fs):>4}  {b}   " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
            print()

    if args.report and findings:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            f.write("# Content triage\n\nGenerated by `audit.py --report`. Each item is a prompt for a human "
                    "reader to check against the cited page; none is a verdict.\n\n")
            for b in sorted(findings, key=lambda x: -len(findings[x])):
                fs = findings[b]
                if not fs:
                    continue
                f.write(f"## {b} ({len(fs)})\n\n```\n" + "\n".join(x.fmt() for x in fs) + "\n```\n\n")
        print(f"Wrote triage report → {args.report}")

    if args.sheet:
        path = write_sheet(auditor, only, findings.get(only, []))
        print(f"Wrote source sheet → {os.path.relpath(path, VAULT_DIR)}")

    return 1 if (hub_orphans or multiline or out_of_bounds or alias_collisions or search_cfg_errors) else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Audit nabiwiki citations, links and claims against the two canonical EPUBs.")
    ap.add_argument("--reindex", action="store_true", help="rebuild the EPUB page index cache")
    ap.add_argument("--links", action="store_true", help="list every unresolved wikilink target")
    ap.add_argument("--citations", action="store_true", help="list every out-of-bounds citation")
    ap.add_argument("--note", metavar="NAME", help="full content findings for one note")
    ap.add_argument("--content", action="store_true", help="full content findings for every note")
    ap.add_argument("--no-content", action="store_true", help="structural checks only (fast)")
    ap.add_argument("--report", metavar="PATH", help="write the full content triage as Markdown")
    ap.add_argument("--sheet", metavar="NAME", help="write review/<NAME>.sheet.md for a human verifier")
    ap.add_argument("--page", nargs="+", metavar="REF", help="print pages: S|I|B vol:page[-page] … (e.g. S 6:77-78), "
                    "or K|M ḥadīth numbers (prints the report itself)")
    ap.add_argument("--out", metavar="PATH", help="with --page, write the pages to PATH instead of printing them")
    ap.add_argument("--exists", nargs="+", metavar="NAME", help="say which names (titles or aliases) have a note, for linking")
    ap.add_argument("--questions", action="store_true", help="list the notes with open questions in ledger/QUESTIONS.md")
    ap.add_argument("--ledger", action="store_true", help="check that every Arabic snippet in ledger/*.md is verbatim on its page")
    ap.add_argument("--tashkil", action="store_true", help="with --page, keep the vocalisation marks (dropped by default)")
    ap.add_argument("--whole-pages", action="store_true", help="with --page K|M, print the whole pages, not just the report")
    sys.exit(run(ap.parse_args()))
