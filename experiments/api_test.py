#!/usr/bin/env python3
"""
API Diagnostic Test Script
===========================

Tests all ethics corpus APIs and reports:
- Which APIs are reachable
- Response structure (first 500 chars)
- Any errors encountered

Run this first, then send me the output so I can fix the fetcher.

Usage:
    python api_test.py > api_test_results.txt 2>&1
    
Then send me api_test_results.txt
"""

import json
import sys
import time
from datetime import datetime

# Fix Windows encoding issues
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("ERROR: Please install requests: pip install requests")
    sys.exit(1)


def safe_print(msg):
    """Print with encoding safety"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'))


def test_api(name, url, headers=None, method='GET', timeout=15):
    """Test a single API endpoint"""
    safe_print(f"\n{'='*60}")
    safe_print(f"Testing: {name}")
    safe_print(f"URL: {url}")
    safe_print(f"{'='*60}")
    
    try:
        start = time.time()
        
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=timeout)
        else:
            response = requests.post(url, headers=headers, timeout=timeout)
        
        elapsed = time.time() - start
        
        safe_print(f"Status: {response.status_code}")
        safe_print(f"Time: {elapsed:.2f}s")
        safe_print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        
        # Try to parse as JSON
        try:
            data = response.json()
            safe_print(f"JSON Keys: {list(data.keys()) if isinstance(data, dict) else f'Array[{len(data)}]'}")
            
            # Pretty print first bit
            preview = json.dumps(data, indent=2, ensure_ascii=True)[:800]
            safe_print(f"Preview:\n{preview}")
            
            return {"status": "OK", "code": response.status_code, "data": data}
            
        except json.JSONDecodeError:
            # Not JSON, show text preview
            text = response.text[:500]
            safe_print(f"Text Preview:\n{text}")
            return {"status": "OK_TEXT", "code": response.status_code, "text": text}
            
    except requests.exceptions.Timeout:
        safe_print("ERROR: Request timed out")
        return {"status": "TIMEOUT"}
    except requests.exceptions.ConnectionError as e:
        safe_print(f"ERROR: Connection failed - {e}")
        return {"status": "CONNECTION_ERROR", "error": str(e)}
    except Exception as e:
        safe_print(f"ERROR: {type(e).__name__} - {e}")
        return {"status": "ERROR", "error": str(e)}


def main():
    safe_print("=" * 70)
    safe_print("ETHICS CORPUS API DIAGNOSTIC TEST")
    safe_print(f"Timestamp: {datetime.now().isoformat()}")
    safe_print("=" * 70)
    
    results = {}
    
    # =========================================================================
    # 1. SEFARIA (Hebrew/Jewish)
    # =========================================================================
    
    # Test index/TOC
    results['sefaria_index'] = test_api(
        "Sefaria - Index",
        "https://www.sefaria.org/api/index"
    )
    
    # Test shape endpoint
    results['sefaria_shape'] = test_api(
        "Sefaria - Shape (Pirkei Avot)",
        "https://www.sefaria.org/api/shape/Pirkei_Avot"
    )
    
    # Test v3 texts endpoint
    results['sefaria_v3_text'] = test_api(
        "Sefaria - v3/texts (Pirkei Avot 1)",
        "https://www.sefaria.org/api/v3/texts/Pirkei_Avot.1"
    )
    
    # Test alternative text format
    results['sefaria_texts_alt'] = test_api(
        "Sefaria - texts (Pirkei Avot 1:1)",
        "https://www.sefaria.org/api/texts/Pirkei_Avot.1.1"
    )
    
    # =========================================================================
    # 2. QURAN (AlQuran Cloud)
    # =========================================================================
    
    results['quran_editions'] = test_api(
        "Quran - Editions List",
        "https://api.alquran.cloud/v1/edition"
    )
    
    results['quran_surah'] = test_api(
        "Quran - Surah 1 (Al-Fatiha)",
        "https://api.alquran.cloud/v1/surah/1/editions/quran-uthmani,en.asad"
    )
    
    # =========================================================================
    # 3. HADITH (fawazahmed0)
    # =========================================================================
    
    results['hadith_editions'] = test_api(
        "Hadith - Editions List",
        "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.json"
    )
    
    results['hadith_bukhari_1'] = test_api(
        "Hadith - Bukhari #1",
        "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-bukhari/1.json"
    )
    
    # =========================================================================
    # 4. BIBLE API
    # =========================================================================
    
    results['bible_verse'] = test_api(
        "Bible - Matthew 5:1-12",
        "https://bible-api.com/matthew+5:1-12"
    )
    
    results['bible_ot'] = test_api(
        "Bible - Exodus 20:1-17",
        "https://bible-api.com/exodus+20:1-17"
    )
    
    # =========================================================================
    # 5. BHAGAVAD GITA
    # =========================================================================
    
    results['gita_chapters'] = test_api(
        "Gita - Chapters List",
        "https://vedicscriptures.github.io/chapters"
    )
    
    results['gita_chapter2'] = test_api(
        "Gita - Chapter 2",
        "https://vedicscriptures.github.io/chapter/2"
    )
    
    results['gita_verse'] = test_api(
        "Gita - Verse 2.47",
        "https://vedicscriptures.github.io/slok/2/47"
    )
    
    # Alternative Gita API
    results['gita_alt'] = test_api(
        "Gita (bhagavadgitaapi.in) - Chapter 2",
        "https://bhagavadgitaapi.in/slok/2/47"
    )
    
    # =========================================================================
    # 6. COURTLISTENER (requires key but test without)
    # =========================================================================
    
    results['courtlistener_search'] = test_api(
        "CourtListener - Search (no auth)",
        "https://www.courtlistener.com/api/rest/v4/search/?q=contract&type=o"
    )
    
    # =========================================================================
    # 7. CHINESE TEXT PROJECT
    # =========================================================================
    
    results['ctext_gettext'] = test_api(
        "CText - gettext (Analects)",
        "https://ctext.org/api/gettext?urn=ctp:analects/xue-er"
    )
    
    # =========================================================================
    # 8. SUTTACENTRAL (Buddhist)
    # =========================================================================
    
    results['suttacentral_sutta'] = test_api(
        "SuttaCentral - Sutta Info (DN31)",
        "https://suttacentral.net/api/suttaplex/dn31"
    )
    
    results['suttacentral_text'] = test_api(
        "SuttaCentral - Text (DN31)",
        "https://suttacentral.net/api/bilarasuttas/dn31/sujato"
    )
    
    # =========================================================================
    # 9. INDICA (Rig Veda)
    # =========================================================================
    
    results['indica_rv'] = test_api(
        "Indica - Rig Veda metadata",
        "https://aninditabasu.github.io/indica/rv.json"
    )
    
    # =========================================================================
    # 10. THEAUM GITA API
    # =========================================================================
    
    results['theaum_gita'] = test_api(
        "TheAum - Gita API",
        "https://gita.theaum.org/api/"
    )
    
    results['theaum_verse'] = test_api(
        "TheAum - Verse 2.47",
        "https://gita.theaum.org/api/chapter/2/verse/47"
    )
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    
    safe_print("\n" + "=" * 70)
    safe_print("SUMMARY")
    safe_print("=" * 70)
    
    working = []
    failed = []
    
    for name, result in results.items():
        status = result.get('status', 'UNKNOWN')
        if status in ['OK', 'OK_TEXT']:
            working.append(name)
            safe_print(f"  [OK] {name}")
        else:
            failed.append(name)
            safe_print(f"  [FAIL] {name}: {status}")
    
    safe_print(f"\nWorking: {len(working)}/{len(results)}")
    safe_print(f"Failed: {len(failed)}/{len(results)}")
    
    # Save detailed results
    safe_print("\n" + "=" * 70)
    safe_print("Saving detailed results to api_test_results.json...")
    
    # Convert to serializable format
    serializable = {}
    for k, v in results.items():
        serializable[k] = {
            'status': v.get('status'),
            'code': v.get('code'),
            'error': v.get('error'),
            'has_data': 'data' in v,
            'data_type': type(v.get('data')).__name__ if 'data' in v else None,
        }
    
    with open('api_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(serializable, f, indent=2)
    
    safe_print("Done! Please send me the output above.")


if __name__ == "__main__":
    main()
