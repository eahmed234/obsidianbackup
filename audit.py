#!/usr/bin/env python3
"""
audit.py — Knowledge graph integrity and primary source verification tool for nabiwiki.

Verifies:
1. Canonical EPUB citation validity (Subul al-Hudā & al-Iṣābah volume:page bounds).
2. Knowledge graph link integrity (unresolved wikilinks, fuzzy match recommendations).
3. The Sīrah hub index completeness (detects orphaned notes).
4. Frontmatter schema and required field presence.
"""

import sys
import os
import glob
import re
import json
import zipfile
import difflib
import argparse

VAULT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_DIR = os.path.join(VAULT_DIR, "sources")
CACHE_FILE = os.path.join(SOURCES_DIR, ".index_cache.json")

SUBUL_EPUB = os.path.join(SOURCES_DIR, "1693.epub")
ISABAH_EPUB = os.path.join(SOURCES_DIR, "9767.epub")

PAGE_RE = re.compile(r"الجزء:\s*(\d+)\s*-\s*الصفحة:\s*(\d+)")

def get_epub_mtime(epub_path):
    try:
        return os.path.getmtime(epub_path)
    except OSError:
        return 0

def build_epub_index(epub_path, name):
    if not os.path.isfile(epub_path):
        print(f"Warning: {epub_path} not found. Skipping {name} index.")
        return {}
    
    print(f"Indexing {name} from {os.path.basename(epub_path)}...")
    index = {} # "vol:page" -> internal_path
    vol_max_pages = {} # vol -> max_page
    
    with zipfile.ZipFile(epub_path, "r") as z:
        for fname in z.namelist():
            if not fname.startswith("OEBPS/text/"):
                continue
            data = z.read(fname).decode("utf-8", errors="ignore")
            match = PAGE_RE.search(data)
            if match:
                vol = int(match.group(1))
                page = int(match.group(2))
                key = f"{vol}:{page}"
                index[key] = fname
                if vol not in vol_max_pages or page > vol_max_pages[vol]:
                    vol_max_pages[vol] = page
                    
    return {
        "pages": index,
        "max_pages": vol_max_pages,
        "mtime": get_epub_mtime(epub_path)
    }

def load_or_build_indices(force_reindex=False):
    cache = {}
    if os.path.isfile(CACHE_FILE) and not force_reindex:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    subul_valid = (
        "subul" in cache
        and cache["subul"].get("mtime") == get_epub_mtime(SUBUL_EPUB)
        and len(cache["subul"].get("pages", {})) > 0
    )
    isabah_valid = (
        "isabah" in cache
        and cache["isabah"].get("mtime") == get_epub_mtime(ISABAH_EPUB)
        and len(cache["isabah"].get("pages", {})) > 0
    )

    updated = False
    if not subul_valid:
        cache["subul"] = build_epub_index(SUBUL_EPUB, "Subul al-Hudā")
        updated = True
    if not isabah_valid:
        cache["isabah"] = build_epub_index(ISABAH_EPUB, "al-Iṣābah")
        updated = True

    if updated:
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except Exception as e:
            print(f"Warning: Could not save index cache: {e}")

    return cache.get("subul", {}), cache.get("isabah", {})

def parse_frontmatter(content):
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return None, content
    fm_text = fm_match.group(1)
    body = content[fm_match.end():]
    
    data = {}
    # Simple line-by-line YAML parser for common vault keys
    current_list_key = None
    for line in fm_text.splitlines():
        # check list item
        list_match = re.match(r"^\s*-\s+(.+)$", line)
        if list_match and current_list_key:
            val = list_match.group(1).strip().strip("\"'\''")
            data.setdefault(current_list_key, []).append(val)
            continue
        
        kv_match = re.match(r"^([a-zA-Z0-9_]+):\s*(.*)$", line)
        if kv_match:
            key = kv_match.group(1)
            val = kv_match.group(2).strip()
            if not val:
                current_list_key = key
                data[key] = []
            else:
                current_list_key = None
                # Clean quotes
                val_clean = val.strip("\"'\''")
                # Handle inline bracket list: [a, b]
                if val.startswith("[") and val.endswith("]"):
                    items = [x.strip().strip("\"'\''") for x in val[1:-1].split(",") if x.strip()]
                    data[key] = items
                else:
                    data[key] = val_clean
        else:
            current_list_key = None

    return data, body

def run_audit(args):
    print("=== Nabiwiki Knowledge Graph & Citation Audit ===\n")
    subul_idx, isabah_idx = load_or_build_indices(force_reindex=args.reindex)

    subul_pages = set(subul_idx.get("pages", {}).keys())
    isabah_pages = set(isabah_idx.get("pages", {}).keys())

    all_md_files = [
        f for f in glob.glob(os.path.join(VAULT_DIR, "*.md"))
        if os.path.basename(f) not in ["GEMINI.md", "CLAUDE.md", "README.md"]
    ]

    all_notes = {}  # basename -> {file, fm, body}
    aliases_map = {} # alias -> canonical note basename

    for fpath in all_md_files:
        bname = os.path.splitext(os.path.basename(fpath))[0]
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        fm, body = parse_frontmatter(content)
        all_notes[bname] = {
            "path": fpath,
            "fm": fm or {},
            "body": body,
            "raw": content
        }
        aliases_map[bname] = bname
        if fm:
            aliases = fm.get("aliases", [])
            if isinstance(aliases, list):
                for a in aliases:
                    if a and isinstance(a, str):
                        aliases_map[a.strip()] = bname
            elif isinstance(aliases, str):
                aliases_map[aliases.strip()] = bname

    total_notes = len(all_notes)
    print(f"Total Content Notes: {total_notes}")
    print(f"Indexed Subul al-Hudā Pages: {len(subul_pages)}")
    print(f"Indexed al-Iṣābah Pages: {len(isabah_pages)}\n")

    # 1. Check The Sīrah Hub Completeness
    hub_orphans = []
    the_sirah_note = all_notes.get("The Sīrah")
    if the_sirah_note:
        hub_links = set(re.findall(r"\[\[([^\|\]#]+)(?:#[^\|\]]+)?(?:\|[^\]]+)?\]\]", the_sirah_note["raw"]))
        for bname in all_notes:
            if bname != "The Sīrah" and bname not in hub_links:
                hub_orphans.append(bname)

    # 2. Check Wikilinks across all notes
    total_wikilinks = 0
    unresolved_links = {} # target -> list of source files
    multiline_links = []  # (source_file, snippet)

    for bname, note_data in all_notes.items():
        content = note_data["raw"]
        
        # Check for newline inside wikilink syntax
        for bad_link in re.findall(r"\[\[[^\]]*\n[^\]]*\]\]", content):
            multiline_links.append((bname, bad_link.replace("\n", "\\n")))

        links = re.findall(r"\[\[([^\|\]#\n]+)(?:#[^\|\]]+)?(?:\|[^\]]+)?\]\]", content)
        for target in links:
            total_wikilinks += 1
            target_clean = target.strip()
            if target_clean not in aliases_map:
                unresolved_links.setdefault(target_clean, []).append(bname)

    # 3. Citation Verification
    subul_citations_total = 0
    subul_citations_invalid = [] # (bname, vol:page, match_text)
    isabah_citations_total = 0
    isabah_citations_invalid = []

    # Comprehensive citation patterns for Subul al-Hudā and al-Iṣābah
    subul_patterns = [
        re.compile(r"Subul al-Hudā[^*()\[\]]*?[*\]\s,]+(?:vol\.?\s*)?(\d+):(\d+)", re.IGNORECASE),
        re.compile(r"Subul al-Hudā[^*()\[\]]*?[*\]\s,]+\(?vol\.?\s*(\d+),\s*pp?\.?\s*(\d+)", re.IGNORECASE)
    ]
    isabah_patterns = [
        re.compile(r"al-Iṣābah[^*()\[\]]*?[*\]\s,]+(?:(?:entry\s*)?no\.?\s*\d+\s*[\[\(])?(?:vol\.?\s*)?(\d+):(\d+)", re.IGNORECASE),
        re.compile(r"al-Iṣābah[^*()\[\]]*?[*\]\s,]+\(?vol\.?\s*(\d+),\s*pp?\.?\s*(\d+)", re.IGNORECASE)
    ]

    for bname, note_data in all_notes.items():
        content = note_data["raw"]
        
        # Subul citations
        for pat in subul_patterns:
            for m in pat.finditer(content):
                subul_citations_total += 1
                vol = int(m.group(1))
                page = int(m.group(2))
                key = f"{vol}:{page}"
                if subul_pages and key not in subul_pages:
                    subul_citations_invalid.append((bname, key, m.group(0)))

        # al-Isabah citations
        for pat in isabah_patterns:
            for m in pat.finditer(content):
                isabah_citations_total += 1
                vol = int(m.group(1))
                page = int(m.group(2))
                key = f"{vol}:{page}"
                if isabah_pages and key not in isabah_pages:
                    isabah_citations_invalid.append((bname, key, m.group(0)))

    # 4. Frontmatter Schema Check
    missing_fm = []
    missing_primary_source = []
    missing_required_fields = []

    for bname, note_data in all_notes.items():
        fm = note_data["fm"]
        if not fm:
            missing_fm.append(bname)
            continue
        
        for req in ["title", "arabic", "type", "tags"]:
            if req not in fm:
                missing_required_fields.append((bname, req))

        if fm.get("type") not in ["index", "source"]:
            if "primary_source" not in fm:
                missing_primary_source.append(bname)

    # --- Print Summary Report ---
    print("-" * 50)
    print("AUDIT SUMMARY RESULTS")
    print("-" * 50)
    print(f"Hub Completeness: {'PASS (0 orphans)' if not hub_orphans else f'FAIL ({len(hub_orphans)} orphans)'}")
    print(f"Multiline Wrapped Links: {'PASS (0)' if not multiline_links else f'FAIL ({len(multiline_links)})'}")
    print(f"Wikilinks Total: {total_wikilinks} | Unresolved: {len(unresolved_links)}")
    print(f"Subul al-Hudā Citations: {subul_citations_total} | Out-of-bounds: {len(subul_citations_invalid)}")
    print(f"al-Iṣābah Citations: {isabah_citations_total} | Out-of-bounds: {len(isabah_citations_invalid)}")
    print(f"Frontmatter Integrity: Missing FM: {len(missing_fm)} | Missing Primary Source: {len(missing_primary_source)}")
    print("-" * 50 + "\n")

    # Detailed reports
    if hub_orphans:
        print(f"🚨 Orphaned Notes not in The Sīrah.md ({len(hub_orphans)}):")
        for o in sorted(hub_orphans):
            print(f"  - [[{o}]]")
        print()

    if multiline_links:
        print(f"🚨 Wrapped Links containing line breaks ({len(multiline_links)}):")
        for bname, snip in multiline_links:
            print(f"  - {bname}: {snip}")
        print()

    if subul_citations_invalid:
        print(f"🚨 Invalid Subul al-Hudā Citations ({len(subul_citations_invalid)}):")
        for bname, cite, snip in subul_citations_invalid[:15]:
            print(f"  - {bname}: {snip} (Page {cite} not in 1693.epub)")
        if len(subul_citations_invalid) > 15:
            print(f"  ... and {len(subul_citations_invalid) - 15} more")
        print()

    if isabah_citations_invalid:
        print(f"🚨 Invalid al-Iṣābah Citations ({len(isabah_citations_invalid)}):")
        for bname, cite, snip in isabah_citations_invalid[:15]:
            print(f"  - {bname}: {snip} (Page {cite} not in 9767.epub)")
        if len(isabah_citations_invalid) > 15:
            print(f"  ... and {len(isabah_citations_invalid) - 15} more")
        print()

    if args.links or len(unresolved_links) > 0:
        print(f"🔍 Top Unresolved Wikilink Targets ({len(unresolved_links)} total):")
        sorted_unresolved = sorted(unresolved_links.items(), key=lambda x: -len(x[1]))
        candidate_pool = list(all_notes.keys()) + list(aliases_map.keys())

        shown = 0
        for target, sources in sorted_unresolved:
            if not args.links and shown >= 25:
                print(f"  ... ({len(sorted_unresolved) - 25} more unresolved targets. Run with --links to see all)")
                break
            
            # Find close matches
            close = difflib.get_close_matches(target, candidate_pool, n=2, cutoff=0.7)
            suggestion = f" -> did you mean {close}?" if close else ""
            print(f"  - [[{target}]] ({len(sources)} occurrences: {', '.join(sources[:2])}{'...' if len(sources)>2 else ''}){suggestion}")
            shown += 1
        print()

    if missing_primary_source:
        print(f"⚠️ Notes Missing primary_source Frontmatter ({len(missing_primary_source)}):")
        for m in missing_primary_source[:10]:
            print(f"  - {m}")
        if len(missing_primary_source) > 10:
            print(f"  ... and {len(missing_primary_source) - 10} more")
        print()

    exit_code = 1 if (hub_orphans or multiline_links or subul_citations_invalid or isabah_citations_invalid) else 0
    return exit_code

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit nabiwiki citations and link integrity against primary EPUB sources.")
    parser.add_argument("--reindex", action="store_true", help="Force rebuild EPUB page indices.")
    parser.add_argument("--links", action="store_true", help="Display all unresolved wikilinks.")
    parser.add_argument("--citations", action="store_true", help="Display full citation verification output.")
    args = parser.parse_args()
    sys.exit(run_audit(args))
