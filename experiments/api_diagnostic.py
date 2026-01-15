#!/usr/bin/env python3
"""
API Response Structure Diagnostic
=================================

Fetches sample responses from each API and saves the raw JSON
so we can see exactly what structure to expect.

Run: python api_diagnostic.py
Output: api_responses/ directory with JSON files
"""

import json
import os
import sys
from pathlib import Path

if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

import requests

OUT_DIR = Path("api_responses")
OUT_DIR.mkdir(exist_ok=True)

def fetch_and_save(name: str, url: str):
    """Fetch URL and save response"""
    print(f"\n{'='*60}")
    print(f"Fetching: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        r = requests.get(url, timeout=30)
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type', 'unknown')}")
        
        try:
            data = r.json()
            
            # Save full response
            out_file = OUT_DIR / f"{name}.json"
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved to: {out_file}")
            
            # Show structure
            print(f"\nResponse type: {type(data).__name__}")
            if isinstance(data, dict):
                print(f"Top-level keys: {list(data.keys())}")
                for k, v in list(data.items())[:5]:
                    vtype = type(v).__name__
                    if isinstance(v, list):
                        print(f"  {k}: list[{len(v)}]")
                        if v and isinstance(v[0], dict):
                            print(f"    [0] keys: {list(v[0].keys())[:10]}")
                    elif isinstance(v, dict):
                        print(f"  {k}: dict with keys {list(v.keys())[:5]}")
                    else:
                        preview = str(v)[:100]
                        print(f"  {k}: {vtype} = {preview}")
            elif isinstance(data, list):
                print(f"List length: {len(data)}")
                if data:
                    print(f"First item type: {type(data[0]).__name__}")
                    if isinstance(data[0], dict):
                        print(f"First item keys: {list(data[0].keys())[:10]}")
            
            return data
            
        except json.JSONDecodeError:
            print(f"Not JSON. First 500 chars:\n{r.text[:500]}")
            return None
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return None


def main():
    print("="*60)
    print("API RESPONSE STRUCTURE DIAGNOSTIC")
    print("="*60)
    
    # ==========================================================================
    # SEFARIA
    # ==========================================================================
    
    # Index structure
    fetch_and_save("sefaria_index", "https://www.sefaria.org/api/index")
    
    # Shape for a specific text
    fetch_and_save("sefaria_shape_avot", "https://www.sefaria.org/api/shape/Pirkei_Avot")
    
    # v3 text endpoint
    fetch_and_save("sefaria_v3_avot_1", "https://www.sefaria.org/api/v3/texts/Pirkei_Avot.1")
    
    # v2 text endpoint for comparison
    fetch_and_save("sefaria_v2_avot_1", "https://www.sefaria.org/api/texts/Pirkei_Avot.1")
    
    # ==========================================================================
    # HADITH
    # ==========================================================================
    
    # Editions list
    fetch_and_save("hadith_editions", "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.json")
    
    # Try alternate endpoint
    fetch_and_save("hadith_editions_min", "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.min.json")
    
    # Direct hadith fetch
    fetch_and_save("hadith_bukhari_1", "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-bukhari/1.json")
    
    # Section info
    fetch_and_save("hadith_bukhari_info", "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-bukhari.json")
    
    # ==========================================================================
    # GITA
    # ==========================================================================
    
    # Chapters list
    fetch_and_save("gita_chapters", "https://vedicscriptures.github.io/chapters")
    
    # Single chapter
    fetch_and_save("gita_chapter_2", "https://vedicscriptures.github.io/chapter/2.json")
    
    # Single verse
    fetch_and_save("gita_verse_2_47", "https://vedicscriptures.github.io/slok/2/47.json")
    
    # ==========================================================================
    # SUTTACENTRAL (Buddhist)
    # ==========================================================================
    
    # Menu for DN
    fetch_and_save("sutta_menu_dn", "https://suttacentral.net/api/menu/dn")
    
    # Suttaplex info
    fetch_and_save("sutta_plex_dn1", "https://suttacentral.net/api/suttaplex/dn1")
    
    # Bilara text
    fetch_and_save("sutta_bilara_dn1", "https://suttacentral.net/api/bilarasuttas/dn1/sujato")
    
    # Try alternate text endpoint
    fetch_and_save("sutta_suttas_dn1", "https://suttacentral.net/api/suttas/dn1/sujato")
    
    # ==========================================================================
    # COURTLISTENER
    # ==========================================================================
    
    # Search results
    fetch_and_save("courtlistener_search", "https://www.courtlistener.com/api/rest/v4/search/?q=contract&type=o")
    
    # Opinions endpoint
    fetch_and_save("courtlistener_opinions", "https://www.courtlistener.com/api/rest/v4/opinions/?page_size=5")
    
    # ==========================================================================
    # QURAN (for reference - this one works)
    # ==========================================================================
    
    fetch_and_save("quran_surah_1", "https://api.alquran.cloud/v1/surah/1/editions/quran-uthmani,en.sahih")
    
    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    print(f"Response files saved to: {OUT_DIR.absolute()}")
    print("\nCheck these files to see actual API structures:")
    for f in sorted(OUT_DIR.glob("*.json")):
        size = f.stat().st_size
        print(f"  {f.name}: {size:,} bytes")


if __name__ == "__main__":
    main()
