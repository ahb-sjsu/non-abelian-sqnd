#!/usr/bin/env python3
"""
Dynamic Ethics Corpus Fetcher
=============================

DYNAMIC VERSION - Discovers API structure at runtime, minimal hardcoding.

Design principles:
1. Query API index/metadata endpoints first to learn structure
2. Handle any response format (list, dict, nested)
3. Graceful degradation on errors
4. Cache discovered structure for efficiency

Usage:
    python dynamic_fetcher.py --all
    python dynamic_fetcher.py --all --limit 50
    python dynamic_fetcher.py --sefaria --quran
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.parse
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

# =============================================================================
# WINDOWS COMPATIBILITY
# =============================================================================

if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("ERROR: pip install requests")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fetcher.log', encoding='utf-8', errors='replace')
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Passage:
    """Unified passage format"""
    id: str
    source: str
    ref: str
    title: str
    text_original: str
    text_english: str
    language: str
    category: str
    subcategory: str
    date_composed: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class FetcherConfig:
    output_dir: str = "./corpus"
    rate_limit_delay: float = 1.0
    limit_per_source: Optional[int] = None
    max_items_per_category: int = 100  # Safety limit per category
    courtlistener_api_key: Optional[str] = None


# =============================================================================
# ROBUST HTTP CLIENT
# =============================================================================

class HTTPClient:
    """HTTP client with caching, retries, rate limiting"""
    
    def __init__(self, config: FetcherConfig):
        self.config = config
        self.session = self._create_session()
        self.last_request = 0.0
        self.cache_dir = Path(config.output_dir) / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_session(self) -> requests.Session:
        s = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        s.mount("http://", HTTPAdapter(max_retries=retry))
        s.mount("https://", HTTPAdapter(max_retries=retry))
        s.headers['User-Agent'] = 'EthicsCorpusFetcher/4.0'
        return s
    
    def _rate_limit(self):
        wait = self.config.rate_limit_delay - (time.time() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        self.last_request = time.time()
    
    def _cache_key(self, url: str) -> Path:
        safe = re.sub(r'[^\w\-.]', '_', url)[:150]
        return self.cache_dir / f"{safe}.json"
    
    def get(self, url: str, headers: Dict = None, cache: bool = True) -> Optional[Any]:
        """GET with caching"""
        cache_path = self._cache_key(url)
        
        if cache and cache_path.exists():
            try:
                return json.loads(cache_path.read_text(encoding='utf-8'))
            except:
                pass
        
        self._rate_limit()
        
        try:
            r = self.session.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            if cache:
                try:
                    cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                except:
                    pass
            
            return data
        except Exception as e:
            logger.debug(f"GET failed {url[:60]}: {type(e).__name__}")
            return None
    
    def get_text(self, url: str) -> Optional[str]:
        """GET returning raw text"""
        self._rate_limit()
        try:
            r = self.session.get(url, timeout=30)
            r.raise_for_status()
            return r.text
        except:
            return None


# =============================================================================
# TEXT EXTRACTION UTILITIES
# =============================================================================

def extract_text(data: Any, max_depth: int = 10) -> str:
    """Recursively extract text from any nested structure"""
    if max_depth <= 0:
        return ""
    if data is None:
        return ""
    if isinstance(data, str):
        return data.strip()
    if isinstance(data, (int, float, bool)):
        return ""
    if isinstance(data, list):
        parts = [extract_text(item, max_depth - 1) for item in data]
        return " ".join(p for p in parts if p)
    if isinstance(data, dict):
        # Priority keys for text content
        for key in ['text', 'content', 'body', 'value', 'he', 'en', 'english', 'translation']:
            if key in data:
                result = extract_text(data[key], max_depth - 1)
                if result:
                    return result
        # Fallback: join all string values
        parts = [extract_text(v, max_depth - 1) for v in data.values()]
        return " ".join(p for p in parts if p)
    return ""


def find_text_fields(data: Any, lang_hint: str = None) -> Tuple[str, str]:
    """Find original and English text from any structure"""
    original = ""
    english = ""
    
    if isinstance(data, dict):
        # Look for language-tagged versions
        versions = data.get('versions', data.get('texts', []))
        if isinstance(versions, list):
            for v in versions:
                if isinstance(v, dict):
                    vlang = v.get('language', v.get('lang', ''))
                    vtext = extract_text(v.get('text', v))
                    if vlang in ('en', 'english', 'eng') and not english:
                        english = vtext
                    elif vlang and not original:
                        original = vtext
        
        # Direct field access
        if not original:
            for key in ['he', 'hebrew', 'ar', 'arabic', 'text', 'slok', 'original']:
                if key in data:
                    original = extract_text(data[key])
                    if original:
                        break
        
        if not english:
            for key in ['en', 'english', 'translation', 'trans', 'text_en']:
                if key in data:
                    english = extract_text(data[key])
                    if english:
                        break
            # Try nested translation objects
            for key in ['tej', 'spitr', 'adi', 'purohit', 'gambir', 'sivananda']:
                if key in data and isinstance(data[key], dict):
                    english = data[key].get('et', data[key].get('english', ''))
                    if english:
                        break
    
    elif isinstance(data, list):
        # Array of texts - combine them
        original = extract_text(data)
    
    elif isinstance(data, str):
        original = data
    
    # Fallback
    if not english and original:
        english = original
    if not original and english:
        original = english
    
    return original[:10000], english[:10000]


# =============================================================================
# DYNAMIC SEFARIA FETCHER
# =============================================================================

class SefariaFetcher:
    """
    Dynamically discovers and fetches from Sefaria.
    
    Strategy:
    1. GET /api/index to discover all available texts
    2. Filter to ethics-relevant categories
    3. GET /api/shape/{title} to learn structure
    4. Fetch chapters dynamically
    """
    
    BASE = "https://www.sefaria.org/api"
    
    # Categories that contain ethics-relevant content (loose filter)
    RELEVANT_CATEGORIES = [
        'mishnah', 'talmud', 'midrash', 'halakhah', 'mussar',
        'musar', 'ethics', 'avot', 'bava', 'sanhedrin', 'nedarim',
        'shevuot', 'ketubot', 'gittin', 'kiddushin'
    ]
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "sefaria"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[SEFARIA] Discovering available texts...")
        
        # Step 1: Get index to discover texts
        index = self.client.get(f"{self.BASE}/index")
        if not index:
            logger.warning("  Could not fetch index, using fallback texts")
            return self._fetch_fallback_texts()
        
        # Step 2: Find relevant texts
        relevant_texts = self._find_relevant_texts(index)
        logger.info(f"  Found {len(relevant_texts)} relevant texts")
        
        # Step 3: Fetch each text
        passages = []
        for title, category in relevant_texts:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            logger.info(f"  Fetching: {title}")
            try:
                text_passages = self._fetch_text(title, category)
                passages.extend(text_passages)
            except Exception as e:
                logger.debug(f"    Error: {e}")
        
        self._save(passages)
        logger.info(f"  [DONE] Sefaria: {len(passages)} passages")
        return passages
    
    def _find_relevant_texts(self, index: Any) -> List[Tuple[str, str]]:
        """Recursively search index for relevant texts"""
        results = []
        
        def search(node, path=""):
            if isinstance(node, dict):
                title = node.get('title', node.get('heTitle', ''))
                cats = node.get('categories', [])
                cat_str = '/'.join(cats).lower() if cats else path.lower()
                
                # Check if relevant
                if title and any(kw in cat_str or kw in title.lower() for kw in self.RELEVANT_CATEGORIES):
                    results.append((title, cat_str))
                
                # Recurse into contents
                for key in ['contents', 'books', 'texts']:
                    if key in node:
                        search(node[key], cat_str)
            
            elif isinstance(node, list):
                for item in node:
                    search(item, path)
        
        search(index)
        
        # Limit to reasonable number
        return results[:30]
    
    def _fetch_text(self, title: str, category: str) -> List[Passage]:
        """Fetch a text, discovering its structure dynamically"""
        passages = []
        
        # Get shape to understand structure
        safe_title = title.replace(' ', '_')
        shape = self.client.get(f"{self.BASE}/shape/{safe_title}")
        
        # Determine number of sections
        if isinstance(shape, list):
            num_sections = len(shape)
        elif isinstance(shape, dict):
            num_sections = shape.get('length', shape.get('chapters', 10))
        else:
            num_sections = 10
        
        num_sections = min(num_sections, self.config.max_items_per_category)
        
        # Fetch sections
        for section in range(1, num_sections + 1):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            # Try v3 API first, fall back to v2
            data = self.client.get(f"{self.BASE}/v3/texts/{safe_title}.{section}")
            if not data:
                data = self.client.get(f"{self.BASE}/texts/{safe_title}.{section}")
            
            if not data:
                continue
            
            original, english = find_text_fields(data)
            if not original and not english:
                continue
            
            ref = data.get('ref', f"{title} {section}")
            
            passages.append(Passage(
                id=f"sefaria:{safe_title}.{section}",
                source="sefaria",
                ref=ref,
                title=title,
                text_original=original,
                text_english=english,
                language="he",
                category=category.split('/')[0] if '/' in category else category,
                subcategory=category,
                date_composed="Talmudic era",
                metadata={"section": section}
            ))
        
        return passages
    
    def _fetch_fallback_texts(self) -> List[Passage]:
        """Fallback if index fails"""
        fallbacks = ["Pirkei_Avot", "Mishnah_Bava_Kamma", "Mishnah_Bava_Metzia"]
        passages = []
        for title in fallbacks:
            passages.extend(self._fetch_text(title, "ethics"))
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# DYNAMIC QURAN FETCHER
# =============================================================================

class QuranFetcher:
    """
    Dynamically fetches Quran from AlQuran Cloud.
    
    Strategy:
    1. GET /edition to discover available editions
    2. GET /meta to learn structure (114 surahs)
    3. Fetch surahs with paired Arabic + English
    """
    
    BASE = "https://api.alquran.cloud/v1"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "quran"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[QURAN] Discovering structure...")
        
        # Get metadata to learn structure
        meta = self.client.get(f"{self.BASE}/meta")
        
        if meta and meta.get('code') == 200:
            surahs_meta = meta.get('data', {}).get('surahs', {}).get('references', [])
            num_surahs = len(surahs_meta) if surahs_meta else 114
        else:
            num_surahs = 114
        
        logger.info(f"  Found {num_surahs} surahs")
        
        # Find best editions
        editions = self.client.get(f"{self.BASE}/edition")
        arabic_edition = "quran-uthmani"
        english_edition = "en.asad"
        
        if editions and editions.get('code') == 200:
            for ed in editions.get('data', []):
                if ed.get('identifier') == 'en.sahih':
                    english_edition = 'en.sahih'
                    break
        
        logger.info(f"  Using editions: {arabic_edition}, {english_edition}")
        
        # Fetch surahs
        passages = []
        for surah_num in range(1, min(num_surahs + 1, self.config.max_items_per_category)):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            logger.info(f"  Surah {surah_num}")
            
            url = f"{self.BASE}/surah/{surah_num}/editions/{arabic_edition},{english_edition}"
            data = self.client.get(url)
            
            if not data or data.get('code') != 200:
                continue
            
            editions_data = data.get('data', [])
            if len(editions_data) < 2:
                continue
            
            ar_data, en_data = editions_data[0], editions_data[1]
            surah_name = ar_data.get('englishName', f'Surah {surah_num}')
            ar_ayahs = ar_data.get('ayahs', [])
            en_ayahs = en_data.get('ayahs', [])
            
            # Chunk into passages
            chunk_size = 10
            for i in range(0, len(ar_ayahs), chunk_size):
                ar_chunk = ar_ayahs[i:i + chunk_size]
                en_chunk = en_ayahs[i:i + chunk_size] if i < len(en_ayahs) else []
                
                ar_text = " ".join(a.get('text', '') for a in ar_chunk)
                en_text = " ".join(a.get('text', '') for a in en_chunk)
                
                start = ar_chunk[0].get('numberInSurah', 1) if ar_chunk else 1
                end = ar_chunk[-1].get('numberInSurah', 1) if ar_chunk else 1
                
                passages.append(Passage(
                    id=f"quran:{surah_num}:{start}-{end}",
                    source="quran",
                    ref=f"Quran {surah_num}:{start}-{end}",
                    title=surah_name,
                    text_original=ar_text,
                    text_english=en_text,
                    language="ar",
                    category="scripture",
                    subcategory="quran",
                    date_composed="610-632 CE",
                    metadata={"surah": surah_num, "revelation": ar_data.get('revelationType', '')}
                ))
        
        self._save(passages)
        logger.info(f"  [DONE] Quran: {len(passages)} passages")
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# DYNAMIC HADITH FETCHER
# =============================================================================

class HadithFetcher:
    """
    Dynamically fetches from Hadith API.
    
    Strategy:
    1. GET /editions.json to discover all collections
    2. For each collection, iterate through hadiths
    """
    
    BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "hadith"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[HADITH] Discovering collections...")
        
        # Discover available editions
        editions = self.client.get(f"{self.BASE}/editions.json")
        
        if not editions:
            logger.warning("  Could not fetch editions list")
            return []
        
        # Find English editions
        eng_editions = []
        for key, info in editions.items():
            if key.startswith('eng-'):
                name = info.get('name', key) if isinstance(info, dict) else key
                eng_editions.append((key, name))
        
        logger.info(f"  Found {len(eng_editions)} English collections")
        
        # Fetch from each collection
        passages = []
        for edition_id, edition_name in eng_editions[:5]:  # Limit to top 5 collections
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            logger.info(f"  Collection: {edition_name}")
            
            # Try to get info about this edition
            info = self.client.get(f"{self.BASE}/editions/{edition_id}.json")
            if info:
                # Get section/hadith info
                sections = info.get('sections', info.get('hadiths', {}))
                if isinstance(sections, dict):
                    total = sum(sections.values()) if sections else 100
                else:
                    total = 100
            else:
                total = 100
            
            total = min(total, self.config.max_items_per_category)
            
            # Fetch hadiths
            count = 0
            for num in range(1, total + 1):
                if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                    break
                
                data = self.client.get(f"{self.BASE}/editions/{edition_id}/{num}.json")
                if not data:
                    continue
                
                hadiths = data.get('hadiths', [data] if 'text' in data else [])
                for h in hadiths:
                    text = h.get('text', '')
                    if not text:
                        continue
                    
                    passages.append(Passage(
                        id=f"hadith:{edition_id}:{num}",
                        source="hadith",
                        ref=f"{edition_name} #{num}",
                        title=edition_name,
                        text_original=text,
                        text_english=text,
                        language="en",
                        category="hadith",
                        subcategory=edition_id,
                        date_composed="~850 CE",
                        metadata={"number": num, "grades": h.get('grades', [])}
                    ))
                    count += 1
                    break  # One hadith per number
            
            logger.info(f"    Retrieved {count} hadiths")
        
        self._save(passages)
        logger.info(f"  [DONE] Hadith: {len(passages)} passages")
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# DYNAMIC BIBLE FETCHER
# =============================================================================

class BibleFetcher:
    """
    Fetches from Bible API.
    Note: This API doesn't have a discovery endpoint, so we use
    a curated list of ethics-relevant references.
    """
    
    BASE = "https://bible-api.com"
    
    # These are canonical references - minimal hardcoding needed
    ETHICS_REFS = [
        "exodus+20:1-17", "leviticus+19:1-18", "deuteronomy+6:4-9",
        "micah+6:6-8", "amos+5:21-24", "isaiah+1:16-17",
        "matthew+5:1-48", "matthew+6:1-34", "matthew+7:1-12",
        "romans+12:1-21", "romans+13:1-14",
        "1corinthians+13:1-13", "galatians+5:16-26",
        "james+1:19-27", "james+2:1-26",
        "1john+3:11-24", "1john+4:7-21",
    ]
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "bible"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[BIBLE] Fetching passages...")
        
        passages = []
        for ref in self.ETHICS_REFS:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            display_ref = ref.replace('+', ' ')
            logger.info(f"  {display_ref}")
            
            data = self.client.get(f"{self.BASE}/{ref}")
            if not data:
                continue
            
            text = data.get('text', '')
            if not text:
                continue
            
            passages.append(Passage(
                id=f"bible:{ref}",
                source="bible",
                ref=data.get('reference', display_ref),
                title=display_ref.split()[0].title(),
                text_original=text,
                text_english=text,
                language="en",
                category="scripture",
                subcategory="bible",
                date_composed="Various",
                metadata={
                    "translation": data.get('translation_name', 'WEB'),
                    "verses": len(data.get('verses', []))
                }
            ))
        
        self._save(passages)
        logger.info(f"  [DONE] Bible: {len(passages)} passages")
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# DYNAMIC GITA FETCHER
# =============================================================================

class GitaFetcher:
    """
    Dynamically fetches Bhagavad Gita.
    
    Strategy:
    1. GET /chapters to discover all chapters
    2. For each chapter, get verse count
    3. Fetch verses
    """
    
    BASE = "https://vedicscriptures.github.io"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "gita"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[GITA] Discovering chapters...")
        
        # Get chapters list
        chapters = self.client.get(f"{self.BASE}/chapters")
        
        if isinstance(chapters, list):
            num_chapters = len(chapters)
        elif isinstance(chapters, dict):
            num_chapters = chapters.get('count', 18)
        else:
            num_chapters = 18
        
        logger.info(f"  Found {num_chapters} chapters")
        
        passages = []
        for ch_num in range(1, min(num_chapters + 1, 19)):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            logger.info(f"  Chapter {ch_num}")
            
            # Get chapter info
            ch_data = self.client.get(f"{self.BASE}/chapter/{ch_num}.json")
            if not ch_data:
                continue
            
            ch_name = ch_data.get('name', ch_data.get('translation', f'Chapter {ch_num}'))
            verses_count = ch_data.get('verses_count', 20)
            
            # Fetch verses
            for v_num in range(1, min(verses_count + 1, self.config.max_items_per_category)):
                if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                    break
                
                v_data = self.client.get(f"{self.BASE}/slok/{ch_num}/{v_num}.json")
                if not v_data:
                    continue
                
                original, english = find_text_fields(v_data)
                if not original and not english:
                    # Try specific fields
                    original = v_data.get('slok', '')
                    for key in ['tej', 'spitr', 'adi', 'gambir', 'sivananda', 'purohit']:
                        if key in v_data and isinstance(v_data[key], dict):
                            english = v_data[key].get('et', '')
                            if english:
                                break
                
                if not original and not english:
                    continue
                
                passages.append(Passage(
                    id=f"gita:{ch_num}:{v_num}",
                    source="gita",
                    ref=f"Bhagavad Gita {ch_num}.{v_num}",
                    title=ch_name,
                    text_original=original,
                    text_english=english,
                    language="sa",
                    category="scripture",
                    subcategory="gita",
                    date_composed="~200 BCE",
                    metadata={
                        "chapter": ch_num,
                        "verse": v_num,
                        "transliteration": v_data.get('transliteration', '')
                    }
                ))
        
        self._save(passages)
        logger.info(f"  [DONE] Gita: {len(passages)} passages")
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# DYNAMIC SUTTACENTRAL FETCHER
# =============================================================================

class SuttaCentralFetcher:
    """
    Dynamically fetches from SuttaCentral.
    
    Strategy:
    1. Use known nikaya structure (DN, MN, SN, AN)
    2. Query API to get available suttas
    3. Fetch text
    """
    
    BASE = "https://suttacentral.net/api"
    
    # Major collections with ethics content
    NIKAYAS = ['dn', 'mn', 'sn', 'an']
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "buddhist"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[BUDDHIST] Discovering suttas...")
        
        passages = []
        
        for nikaya in self.NIKAYAS:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            logger.info(f"  Nikaya: {nikaya.upper()}")
            
            # Get list of suttas in this nikaya
            menu = self.client.get(f"{self.BASE}/menu/{nikaya}")
            
            sutta_ids = []
            if menu:
                sutta_ids = self._extract_sutta_ids(menu, nikaya)
            
            if not sutta_ids:
                # Fallback: try numbered approach
                sutta_ids = [f"{nikaya}{i}" for i in range(1, 20)]
            
            logger.info(f"    Found {len(sutta_ids)} suttas")
            
            for sutta_id in sutta_ids[:self.config.max_items_per_category]:
                if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                    break
                
                # Get sutta info
                info = self.client.get(f"{self.BASE}/suttaplex/{sutta_id}")
                
                title = sutta_id
                if info and isinstance(info, list) and len(info) > 0:
                    info = info[0]
                    title = info.get('original_title', '') or info.get('translated_title', '') or sutta_id
                elif isinstance(info, dict):
                    title = info.get('original_title', '') or info.get('translated_title', '') or sutta_id
                
                # Get text
                text_data = self.client.get(f"{self.BASE}/bilarasuttas/{sutta_id}/sujato")
                
                if not text_data:
                    continue
                
                root = text_data.get('root_text', {})
                trans = text_data.get('translation_text', {})
                
                # Combine segments
                original = " ".join(root.get(k, '') for k in sorted(root.keys()))[:5000]
                english = " ".join(trans.get(k, '') for k in sorted(trans.keys()))[:5000]
                
                if not original and not english:
                    continue
                
                passages.append(Passage(
                    id=f"sutta:{sutta_id}",
                    source="suttacentral",
                    ref=sutta_id.upper(),
                    title=title,
                    text_original=original,
                    text_english=english,
                    language="pi",
                    category="scripture",
                    subcategory=nikaya,
                    date_composed="~400 BCE",
                    metadata={"nikaya": nikaya}
                ))
        
        self._save(passages)
        logger.info(f"  [DONE] Buddhist: {len(passages)} passages")
        return passages
    
    def _extract_sutta_ids(self, menu: Any, nikaya: str) -> List[str]:
        """Extract sutta IDs from menu structure"""
        ids = []
        
        def search(node):
            if isinstance(node, dict):
                uid = node.get('uid', node.get('id', ''))
                if uid and uid.startswith(nikaya) and len(uid) <= 10:
                    ids.append(uid)
                for v in node.values():
                    search(v)
            elif isinstance(node, list):
                for item in node:
                    search(item)
        
        search(menu)
        return ids[:50]  # Limit
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# COURTLISTENER FETCHER
# =============================================================================

class CourtListenerFetcher:
    """Fetches US case law from CourtListener"""
    
    BASE = "https://www.courtlistener.com/api/rest/v4"
    
    SEARCHES = ["contract", "negligence", "due process", "fiduciary", "fraud"]
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.api_key = config.courtlistener_api_key
        self.output_dir = Path(config.output_dir) / "courtlistener"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[COURTLISTENER] Searching case law...")
        
        if not self.api_key:
            logger.warning("  No API key - results may be limited")
        
        headers = {"Authorization": f"Token {self.api_key}"} if self.api_key else {}
        
        passages = []
        for query in self.SEARCHES:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            logger.info(f"  Query: {query}")
            
            url = f"{self.BASE}/search/?q={urllib.parse.quote(query)}&type=o"
            data = self.client.get(url, headers=headers, cache=False)
            
            if not data:
                continue
            
            results = data.get('results', [])
            
            for r in results[:10]:
                snippet = r.get('snippet', '').replace('<mark>', '').replace('</mark>', '')
                if not snippet:
                    continue
                
                passages.append(Passage(
                    id=f"cl:{r.get('id', '')}",
                    source="courtlistener",
                    ref=r.get('caseName', 'Unknown'),
                    title=r.get('caseName', 'Case'),
                    text_original=snippet,
                    text_english=snippet,
                    language="en",
                    category="legal",
                    subcategory=query,
                    date_composed=r.get('dateFiled', 'Unknown'),
                    metadata={"court": r.get('court', ''), "query": query}
                ))
        
        self._save(passages)
        logger.info(f"  [DONE] CourtListener: {len(passages)} passages")
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# EMBEDDED SAMPLES (for APIs without discovery)
# =============================================================================

class EmbeddedFetcher:
    """Provides high-quality embedded samples for sources without APIs"""
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.config = config
        self.output_dir = Path(config.output_dir) / "embedded"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[EMBEDDED] Loading curated samples...")
        
        passages = []
        passages.extend(self._chinese())
        passages.extend(self._greek_roman())
        passages.extend(self._roman_law())
        
        self._save(passages)
        logger.info(f"  [DONE] Embedded: {len(passages)} passages")
        return passages
    
    def _chinese(self) -> List[Passage]:
        data = [
            ("Analects 4:15", "The Master said: 'My teaching contains one principle that runs through it all.' 'What is it?' asked Zengzi. 'Loyalty and reciprocity, that is all.'", "zh"),
            ("Analects 12:2", "Do not do to others what you would not wish done to yourself.", "zh"),
            ("Analects 15:24", "Is there one word that can serve as a principle for life? Perhaps reciprocity: Do not do to others what you would not want done to yourself.", "zh"),
            ("Tao Te Ching 63", "Respond to injury with virtue.", "zh"),
            ("Mencius 7A:4", "If one acts with strong commitment to reciprocity, there is no closer path to humaneness.", "zh"),
        ]
        return [Passage(
            id=f"chinese:{ref.replace(' ', '_')}",
            source="chinese_classics",
            ref=ref, title=ref.split()[0],
            text_original=text, text_english=text,
            language=lang, category="philosophy", subcategory="confucian",
            date_composed="500-200 BCE", metadata={"embedded": True}
        ) for ref, text, lang in data]
    
    def _greek_roman(self) -> List[Passage]:
        data = [
            ("Aristotle, NE 1094a", "Every art and inquiry aims at some good.", "virtue_ethics"),
            ("Aristotle, NE 1106b", "Virtue is a mean between extremes, determined by reason.", "virtue_ethics"),
            ("Plato, Crito 49b", "We ought not to retaliate or render evil for evil.", "non_retaliation"),
            ("Epictetus, Ench. 1", "Some things are in our control, others not.", "stoic_ethics"),
            ("Marcus Aurelius, Med. 2.1", "All wrongdoing arises from ignorance of good and evil.", "stoic_ethics"),
            ("Seneca, Letters 95", "Show generosity as you would wish to receive it.", "reciprocity"),
        ]
        return [Passage(
            id=f"greek:{ref.replace(' ', '_').replace(',', '')}",
            source="greek_roman",
            ref=ref, title=ref.split(',')[0],
            text_original=text, text_english=text,
            language="grc", category="philosophy", subcategory=cat,
            date_composed="Ancient", metadata={"embedded": True}
        ) for ref, text, cat in data]
    
    def _roman_law(self) -> List[Passage]:
        data = [
            ("D.1.1.1pr", "Law is the art of the good and the fair.", "definition"),
            ("D.1.1.10pr", "Justice is the constant will to render each their right.", "justice"),
            ("D.1.1.10.1", "Live honestly, harm no one, give each their due.", "precepts"),
            ("D.50.17.185", "There is no obligation to do the impossible.", "impossibility"),
            ("D.12.6.14", "No one should be enriched at another's expense.", "enrichment"),
        ]
        return [Passage(
            id=f"digest:{ref}",
            source="roman_law",
            ref=f"Digest {ref}", title="Justinian's Digest",
            text_original=text, text_english=text,
            language="la", category="legal", subcategory=cat,
            date_composed="533 CE", metadata={"embedded": True}
        ) for ref, text, cat in data]
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# CORPUS COMBINER
# =============================================================================

class CorpusCombiner:
    def __init__(self, config: FetcherConfig):
        self.output_dir = Path(config.output_dir)
    
    def combine(self) -> Dict[str, Any]:
        all_passages = []
        stats = {"sources": {}}
        
        for source_dir in self.output_dir.iterdir():
            if source_dir.is_dir() and not source_dir.name.startswith('.'):
                passages_file = source_dir / "passages.json"
                if passages_file.exists():
                    data = json.loads(passages_file.read_text(encoding='utf-8'))
                    all_passages.extend(data)
                    stats["sources"][source_dir.name] = len(data)
        
        stats["total"] = len(all_passages)
        stats["timestamp"] = datetime.now().isoformat()
        
        (self.output_dir / "combined_corpus.json").write_text(
            json.dumps(all_passages, indent=2, ensure_ascii=False), encoding='utf-8')
        (self.output_dir / "corpus_stats.json").write_text(
            json.dumps(stats, indent=2), encoding='utf-8')
        
        logger.info("\n=== CORPUS STATISTICS ===")
        logger.info(f"Total: {stats['total']} passages")
        for src, cnt in stats["sources"].items():
            logger.info(f"  {src}: {cnt}")
        
        return stats


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Dynamic Ethics Corpus Fetcher")
    
    parser.add_argument("--all", action="store_true", help="Fetch all sources")
    parser.add_argument("--sefaria", action="store_true")
    parser.add_argument("--quran", action="store_true")
    parser.add_argument("--hadith", action="store_true")
    parser.add_argument("--bible", action="store_true")
    parser.add_argument("--gita", action="store_true")
    parser.add_argument("--buddhist", action="store_true")
    parser.add_argument("--courtlistener", action="store_true")
    parser.add_argument("--embedded", action="store_true")
    
    parser.add_argument("--limit", type=int, help="Max passages per source")
    parser.add_argument("--output", default="./corpus", help="Output directory")
    parser.add_argument("--rate-limit", type=float, default=1.0, help="Delay between requests")
    
    args = parser.parse_args()
    
    if not any([args.all, args.sefaria, args.quran, args.hadith, args.bible,
                args.gita, args.buddhist, args.courtlistener, args.embedded]):
        parser.print_help()
        return
    
    config = FetcherConfig(
        output_dir=args.output,
        rate_limit_delay=args.rate_limit,
        limit_per_source=args.limit,
        courtlistener_api_key=os.environ.get("COURTLISTENER_API_KEY"),
    )
    
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    client = HTTPClient(config)
    
    print("=" * 60)
    print("DYNAMIC ETHICS CORPUS FETCHER")
    print("=" * 60)
    print(f"Output: {config.output_dir}")
    if config.limit_per_source:
        print(f"Limit: {config.limit_per_source} per source")
    print("=" * 60)
    
    fetchers = []
    if args.all or args.sefaria:
        fetchers.append(SefariaFetcher(client, config))
    if args.all or args.quran:
        fetchers.append(QuranFetcher(client, config))
    if args.all or args.hadith:
        fetchers.append(HadithFetcher(client, config))
    if args.all or args.bible:
        fetchers.append(BibleFetcher(client, config))
    if args.all or args.gita:
        fetchers.append(GitaFetcher(client, config))
    if args.all or args.buddhist:
        fetchers.append(SuttaCentralFetcher(client, config))
    if args.all or args.courtlistener:
        fetchers.append(CourtListenerFetcher(client, config))
    if args.all or args.embedded:
        fetchers.append(EmbeddedFetcher(client, config))
    
    for fetcher in fetchers:
        try:
            fetcher.fetch_all()
        except Exception as e:
            logger.error(f"Fetcher failed: {type(fetcher).__name__}: {e}")
    
    combiner = CorpusCombiner(config)
    stats = combiner.combine()
    
    print("\n" + "=" * 60)
    print("[COMPLETE]")
    print("=" * 60)
    print(f"Total: {stats['total']} passages")
    print(f"Output: {config.output_dir}/combined_corpus.json")


if __name__ == "__main__":
    main()
