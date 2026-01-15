#!/usr/bin/env python3
"""
Verbose Ethics Corpus Fetcher
=============================

This version logs detailed response information to help debug
why certain APIs return 0 passages.

Key changes:
- Logs first response from each API to show structure
- More aggressive text extraction
- Multiple fallback strategies per source
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
from typing import List, Dict, Any, Optional, Tuple

# Windows fix
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fetcher_verbose.log', encoding='utf-8', errors='replace')
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Passage:
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
    rate_limit_delay: float = 0.5  # Faster for testing
    limit_per_source: Optional[int] = None
    max_per_category: int = 200
    verbose: bool = True

# =============================================================================
# HTTP CLIENT
# =============================================================================

class HTTPClient:
    def __init__(self, config: FetcherConfig):
        self.config = config
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers['User-Agent'] = 'EthicsCorpusFetcher/5.0'
        self.last_request = 0.0
        self.cache_dir = Path(config.output_dir) / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, url: str, cache: bool = True) -> Optional[Any]:
        # Cache check
        cache_key = re.sub(r'[^\w\-.]', '_', url)[:150]
        cache_path = self.cache_dir / f"{cache_key}.json"
        
        if cache and cache_path.exists():
            try:
                return json.loads(cache_path.read_text(encoding='utf-8'))
            except:
                pass
        
        # Rate limit
        wait = self.config.rate_limit_delay - (time.time() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        self.last_request = time.time()
        
        try:
            r = self.session.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            if cache:
                try:
                    cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                except:
                    pass
            
            return data
        except Exception as e:
            logger.debug(f"GET failed {url[:60]}: {e}")
            return None

# =============================================================================
# TEXT EXTRACTION - More aggressive
# =============================================================================

def extract_any_text(data: Any, max_len: int = 10000) -> str:
    """Aggressively extract text from any structure"""
    if data is None:
        return ""
    if isinstance(data, str):
        return data[:max_len]
    if isinstance(data, (int, float, bool)):
        return ""
    if isinstance(data, list):
        parts = [extract_any_text(x, max_len // len(data) if data else max_len) for x in data[:100]]
        return " ".join(p for p in parts if p)[:max_len]
    if isinstance(data, dict):
        # Try known text keys first
        for key in ['text', 'content', 'body', 'slok', 'verse', 'he', 'en', 'english', 
                    'translation', 'value', 'snippet', 'plain_text', 'html_text']:
            if key in data and data[key]:
                result = extract_any_text(data[key], max_len)
                if result and len(result) > 10:
                    return result
        # Fall back to joining all string values
        parts = []
        for v in data.values():
            if isinstance(v, str) and len(v) > 10:
                parts.append(v)
        if parts:
            return " ".join(parts)[:max_len]
    return ""


def log_structure(name: str, data: Any, depth: int = 2):
    """Log the structure of data for debugging"""
    def describe(obj, d=0):
        indent = "  " * d
        if d >= depth:
            return f"{indent}..."
        if obj is None:
            return f"{indent}None"
        if isinstance(obj, str):
            return f"{indent}str({len(obj)}): {obj[:50]!r}..."
        if isinstance(obj, (int, float, bool)):
            return f"{indent}{type(obj).__name__}: {obj}"
        if isinstance(obj, list):
            if not obj:
                return f"{indent}list[]"
            lines = [f"{indent}list[{len(obj)}]:"]
            lines.append(describe(obj[0], d + 1))
            return "\n".join(lines)
        if isinstance(obj, dict):
            lines = [f"{indent}dict{{{len(obj)} keys}}:"]
            for k in list(obj.keys())[:8]:
                lines.append(f"{indent}  {k}:")
                lines.append(describe(obj[k], d + 1))
            return "\n".join(lines)
        return f"{indent}{type(obj).__name__}"
    
    logger.info(f"\n--- {name} structure ---\n{describe(data)}\n---")


# =============================================================================
# SEFARIA - Fixed version
# =============================================================================

class SefariaFetcher:
    BASE = "https://www.sefaria.org/api"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "sefaria"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logged_sample = False
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[SEFARIA] Starting...")
        
        passages = []
        
        # Get index to find texts
        index = self.client.get(f"{self.BASE}/index")
        if not index:
            logger.error("  Could not fetch index")
            return passages
        
        if self.config.verbose and not self.logged_sample:
            log_structure("sefaria_index", index)
            self.logged_sample = True
        
        # Find all texts (index is a nested structure)
        texts = self._extract_texts(index)
        logger.info(f"  Found {len(texts)} total texts")
        
        # Filter to ethics-relevant (loose filter)
        relevant = [t for t in texts if self._is_relevant(t)]
        logger.info(f"  {len(relevant)} ethics-relevant texts")
        
        # Fetch each text
        for title in relevant[:50]:  # Cap at 50 texts
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            text_passages = self._fetch_text(title)
            if text_passages:
                logger.info(f"  {title}: {len(text_passages)} passages")
                passages.extend(text_passages)
        
        self._save(passages)
        logger.info(f"  [DONE] Sefaria: {len(passages)} total")
        return passages
    
    def _extract_texts(self, index: Any) -> List[str]:
        """Recursively extract all text titles from index"""
        titles = []
        
        def search(node):
            if isinstance(node, dict):
                if 'title' in node:
                    titles.append(node['title'])
                for v in node.values():
                    search(v)
            elif isinstance(node, list):
                for item in node:
                    search(item)
        
        search(index)
        return titles
    
    def _is_relevant(self, title: str) -> bool:
        """Check if title is ethics-relevant"""
        title_lower = title.lower()
        keywords = ['avot', 'bava', 'sanhedrin', 'nedarim', 'shevuot', 'gittin', 
                    'ketubot', 'kiddushin', 'ethics', 'musar', 'mussar', 'derech']
        return any(kw in title_lower for kw in keywords)
    
    def _fetch_text(self, title: str) -> List[Passage]:
        """Fetch all sections of a text"""
        passages = []
        safe_title = title.replace(' ', '_')
        
        # Get shape to know structure
        shape = self.client.get(f"{self.BASE}/shape/{safe_title}")
        
        if shape is None:
            num_sections = 10  # Guess
        elif isinstance(shape, list):
            num_sections = len(shape)
        elif isinstance(shape, dict):
            num_sections = shape.get('length', 10)
        else:
            num_sections = 10
        
        num_sections = min(num_sections, self.config.max_per_category)
        
        # Fetch each section
        for sec in range(1, num_sections + 1):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            # Try v3 API
            data = self.client.get(f"{self.BASE}/v3/texts/{safe_title}.{sec}")
            
            if data and self.config.verbose and len(passages) == 0:
                log_structure(f"sefaria_v3_{safe_title}", data)
            
            if not data:
                # Try v2
                data = self.client.get(f"{self.BASE}/texts/{safe_title}.{sec}")
            
            if not data:
                continue
            
            # Extract text - handle both v2 and v3 formats
            he_text = ""
            en_text = ""
            
            if isinstance(data, dict):
                # v3 format: versions array
                versions = data.get('versions', [])
                for v in versions:
                    if isinstance(v, dict):
                        lang = v.get('language', '')
                        text = extract_any_text(v.get('text', ''))
                        if lang == 'he' and not he_text:
                            he_text = text
                        elif lang == 'en' and not en_text:
                            en_text = text
                
                # v2 format: direct he/text fields
                if not he_text:
                    he_text = extract_any_text(data.get('he', data.get('text', '')))
                if not en_text:
                    en_text = extract_any_text(data.get('text', ''))
            
            if not he_text and not en_text:
                continue
            
            passages.append(Passage(
                id=f"sefaria:{safe_title}.{sec}",
                source="sefaria",
                ref=data.get('ref', f"{title} {sec}"),
                title=title,
                text_original=he_text[:5000],
                text_english=en_text[:5000] if en_text else he_text[:5000],
                language="he",
                category="jewish",
                subcategory=safe_title.split('_')[0].lower(),
                date_composed="Talmudic",
                metadata={"section": sec}
            ))
        
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# HADITH - Fixed version
# =============================================================================

class HadithFetcher:
    BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"
    
    # Known working collections (fallback)
    KNOWN_COLLECTIONS = [
        "eng-bukhari",
        "eng-muslim", 
        "eng-abudawud",
        "eng-tirmidhi",
        "eng-nasai",
        "eng-ibnmajah",
    ]
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "hadith"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[HADITH] Starting...")
        
        # Try to discover editions
        editions = self.client.get(f"{self.BASE}/editions.json")
        
        if editions and self.config.verbose:
            log_structure("hadith_editions", editions)
        
        # Parse editions - handle different formats
        collections = []
        if isinstance(editions, dict):
            for key in editions.keys():
                if 'eng' in key.lower() or 'english' in key.lower():
                    collections.append(key)
        elif isinstance(editions, list):
            for item in editions:
                if isinstance(item, str) and 'eng' in item.lower():
                    collections.append(item)
                elif isinstance(item, dict):
                    name = item.get('name', item.get('collection', ''))
                    if 'eng' in name.lower():
                        collections.append(name)
        
        # Fallback to known collections
        if not collections:
            logger.info("  Using known collections as fallback")
            collections = self.KNOWN_COLLECTIONS
        
        logger.info(f"  Collections: {collections}")
        
        passages = []
        for coll in collections[:5]:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            coll_passages = self._fetch_collection(coll)
            logger.info(f"  {coll}: {len(coll_passages)} hadiths")
            passages.extend(coll_passages)
        
        self._save(passages)
        logger.info(f"  [DONE] Hadith: {len(passages)} total")
        return passages
    
    def _fetch_collection(self, collection: str) -> List[Passage]:
        passages = []
        
        # Get collection info
        info = self.client.get(f"{self.BASE}/editions/{collection}.json")
        
        if info and self.config.verbose and not passages:
            log_structure(f"hadith_{collection}_info", info)
        
        # Determine how many hadiths
        if isinstance(info, dict):
            # Try to find total count
            metadata = info.get('metadata', info)
            total = metadata.get('length', metadata.get('total', 100))
            sections = info.get('sections', {})
            if sections:
                total = sum(sections.values()) if isinstance(sections, dict) else 100
        else:
            total = 100
        
        total = min(total, self.config.max_per_category)
        
        # Fetch hadiths
        for num in range(1, total + 1):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            data = self.client.get(f"{self.BASE}/editions/{collection}/{num}.json")
            
            if not data:
                # Try alternate format
                data = self.client.get(f"{self.BASE}/editions/{collection}/sections/1/{num}.json")
            
            if not data:
                continue
            
            if self.config.verbose and len(passages) == 0:
                log_structure(f"hadith_{collection}_sample", data)
            
            # Extract text
            text = ""
            if isinstance(data, dict):
                hadiths = data.get('hadiths', [data])
                if hadiths and isinstance(hadiths[0], dict):
                    text = hadiths[0].get('text', '')
                if not text:
                    text = extract_any_text(data)
            
            if not text or len(text) < 10:
                continue
            
            passages.append(Passage(
                id=f"hadith:{collection}:{num}",
                source="hadith",
                ref=f"{collection} #{num}",
                title=collection.replace('eng-', '').replace('-', ' ').title(),
                text_original=text,
                text_english=text,
                language="en",
                category="hadith",
                subcategory=collection,
                date_composed="~850 CE",
                metadata={"number": num}
            ))
        
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# GITA - Fixed version
# =============================================================================

class GitaFetcher:
    BASE = "https://vedicscriptures.github.io"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "gita"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[GITA] Starting...")
        
        # Get chapters
        chapters = self.client.get(f"{self.BASE}/chapters")
        
        if chapters and self.config.verbose:
            log_structure("gita_chapters", chapters)
        
        # Determine chapter count
        if isinstance(chapters, list):
            num_chapters = len(chapters)
        elif isinstance(chapters, dict):
            num_chapters = chapters.get('count', 18)
        else:
            num_chapters = 18
        
        logger.info(f"  Chapters: {num_chapters}")
        
        passages = []
        for ch in range(1, num_chapters + 1):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            ch_passages = self._fetch_chapter(ch)
            logger.info(f"  Chapter {ch}: {len(ch_passages)} verses")
            passages.extend(ch_passages)
        
        self._save(passages)
        logger.info(f"  [DONE] Gita: {len(passages)} total")
        return passages
    
    def _fetch_chapter(self, chapter: int) -> List[Passage]:
        passages = []
        
        # Get chapter info
        ch_data = self.client.get(f"{self.BASE}/chapter/{chapter}.json")
        
        if not ch_data:
            return passages
        
        if self.config.verbose and chapter == 1:
            log_structure("gita_chapter_1", ch_data)
        
        ch_name = ch_data.get('name', ch_data.get('translation', f'Chapter {chapter}'))
        verses_count = ch_data.get('verses_count', 20)
        
        # Fetch each verse
        for v in range(1, min(verses_count + 1, self.config.max_per_category)):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            verse = self.client.get(f"{self.BASE}/slok/{chapter}/{v}.json")
            
            if not verse:
                continue
            
            if self.config.verbose and chapter == 1 and v == 1:
                log_structure("gita_verse_1_1", verse)
            
            # Extract Sanskrit (slok field)
            sanskrit = verse.get('slok', '')
            
            # Extract English translation - check multiple commentators
            english = ""
            for commentator in ['tej', 'spitr', 'purohit', 'chinmay', 'san', 'adi', 'gambir', 'sivananda']:
                if commentator in verse:
                    comm = verse[commentator]
                    if isinstance(comm, dict):
                        english = comm.get('et', comm.get('ec', ''))
                    elif isinstance(comm, str):
                        english = comm
                    if english:
                        break
            
            # Fallback
            if not english:
                english = verse.get('transliteration', sanskrit)
            
            if not sanskrit and not english:
                continue
            
            passages.append(Passage(
                id=f"gita:{chapter}:{v}",
                source="gita",
                ref=f"Bhagavad Gita {chapter}.{v}",
                title=ch_name,
                text_original=sanskrit,
                text_english=english if english else sanskrit,
                language="sa",
                category="scripture",
                subcategory="gita",
                date_composed="~200 BCE",
                metadata={
                    "chapter": chapter, 
                    "verse": v,
                    "transliteration": verse.get('transliteration', '')
                }
            ))
        
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# SUTTACENTRAL (Buddhist) - Fixed
# =============================================================================

class SuttaCentralFetcher:
    BASE = "https://suttacentral.net/api"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "buddhist"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[BUDDHIST] Starting...")
        
        passages = []
        
        # Nikayas to search
        nikayas = [
            ('dn', 'Digha Nikaya', 34),
            ('mn', 'Majjhima Nikaya', 152),
            ('sn', 'Samyutta Nikaya', 56),
            ('an', 'Anguttara Nikaya', 11),
        ]
        
        for nikaya, name, max_num in nikayas:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            logger.info(f"  {name}")
            nikaya_passages = self._fetch_nikaya(nikaya, max_num)
            logger.info(f"    Got {len(nikaya_passages)} passages")
            passages.extend(nikaya_passages)
        
        self._save(passages)
        logger.info(f"  [DONE] Buddhist: {len(passages)} total")
        return passages
    
    def _fetch_nikaya(self, nikaya: str, max_num: int) -> List[Passage]:
        passages = []
        
        # Try direct numbered access (dn1, dn2, mn1, mn2, etc)
        for num in range(1, min(max_num + 1, self.config.max_per_category)):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            sutta_id = f"{nikaya}{num}"
            
            # Get suttaplex for title
            plex = self.client.get(f"{self.BASE}/suttaplex/{sutta_id}")
            
            if plex and self.config.verbose and num == 1:
                log_structure(f"sutta_plex_{sutta_id}", plex)
            
            title = sutta_id
            if plex:
                if isinstance(plex, list) and plex:
                    title = plex[0].get('translated_title', plex[0].get('original_title', sutta_id))
                elif isinstance(plex, dict):
                    title = plex.get('translated_title', plex.get('original_title', sutta_id))
            
            # Try bilara API for text
            bilara = self.client.get(f"{self.BASE}/bilarasuttas/{sutta_id}/sujato")
            
            if bilara and self.config.verbose and num == 1:
                log_structure(f"sutta_bilara_{sutta_id}", bilara)
            
            pali = ""
            english = ""
            
            if bilara and isinstance(bilara, dict):
                root = bilara.get('root_text', {})
                trans = bilara.get('translation_text', {})
                
                if root:
                    pali = " ".join(str(v) for v in root.values() if v)[:5000]
                if trans:
                    english = " ".join(str(v) for v in trans.values() if v)[:5000]
            
            # Try alternate endpoint if bilara fails
            if not english:
                alt = self.client.get(f"{self.BASE}/suttas/{sutta_id}/sujato")
                if alt and isinstance(alt, dict):
                    english = alt.get('text', '')
                    if not english:
                        english = extract_any_text(alt)
            
            if not pali and not english:
                continue
            
            passages.append(Passage(
                id=f"sutta:{sutta_id}",
                source="suttacentral",
                ref=sutta_id.upper(),
                title=title,
                text_original=pali if pali else english,
                text_english=english if english else pali,
                language="pi",
                category="scripture",
                subcategory=nikaya,
                date_composed="~400 BCE",
                metadata={"nikaya": nikaya, "number": num}
            ))
        
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# COURTLISTENER - Fixed
# =============================================================================

class CourtListenerFetcher:
    BASE = "https://www.courtlistener.com/api/rest/v4"
    
    SEARCHES = ["contract", "negligence", "due process", "equal protection", "fiduciary duty"]
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.api_key = os.environ.get("COURTLISTENER_API_KEY")
        self.output_dir = Path(config.output_dir) / "courtlistener"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[COURTLISTENER] Starting...")
        
        if not self.api_key:
            logger.warning("  No COURTLISTENER_API_KEY env var - may be limited")
        
        passages = []
        
        for query in self.SEARCHES:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            logger.info(f"  Search: {query}")
            
            url = f"{self.BASE}/search/?q={urllib.parse.quote(query)}&type=o"
            headers = {"Authorization": f"Token {self.api_key}"} if self.api_key else {}
            
            # Don't cache search results
            try:
                r = self.client.session.get(url, headers=headers, timeout=30)
                data = r.json()
            except:
                continue
            
            if self.config.verbose and not passages:
                log_structure("courtlistener_search", data)
            
            results = data.get('results', [])
            logger.info(f"    {len(results)} results")
            
            for r in results[:20]:
                snippet = r.get('snippet', '')
                if snippet:
                    # Clean HTML
                    snippet = re.sub(r'<[^>]+>', '', snippet)
                
                if not snippet or len(snippet) < 50:
                    continue
                
                passages.append(Passage(
                    id=f"cl:{r.get('id', '')}",
                    source="courtlistener",
                    ref=r.get('caseName', 'Unknown Case'),
                    title=r.get('caseName', 'Case'),
                    text_original=snippet,
                    text_english=snippet,
                    language="en",
                    category="legal",
                    subcategory=query.replace(' ', '_'),
                    date_composed=r.get('dateFiled', 'Unknown'),
                    metadata={"court": r.get('court', ''), "query": query}
                ))
        
        self._save(passages)
        logger.info(f"  [DONE] CourtListener: {len(passages)} total")
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# QURAN (reference - already works)
# =============================================================================

class QuranFetcher:
    BASE = "https://api.alquran.cloud/v1"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "quran"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[QURAN] Starting...")
        
        passages = []
        
        for surah in range(1, 115):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            url = f"{self.BASE}/surah/{surah}/editions/quran-uthmani,en.sahih"
            data = self.client.get(url)
            
            if not data or data.get('code') != 200:
                continue
            
            editions = data.get('data', [])
            if len(editions) < 2:
                continue
            
            ar_data, en_data = editions[0], editions[1]
            name = ar_data.get('englishName', f'Surah {surah}')
            ar_ayahs = ar_data.get('ayahs', [])
            en_ayahs = en_data.get('ayahs', [])
            
            # Chunk
            for i in range(0, len(ar_ayahs), 10):
                ar_chunk = ar_ayahs[i:i+10]
                en_chunk = en_ayahs[i:i+10] if i < len(en_ayahs) else []
                
                ar_text = " ".join(a.get('text', '') for a in ar_chunk)
                en_text = " ".join(a.get('text', '') for a in en_chunk)
                
                start = ar_chunk[0].get('numberInSurah', 1) if ar_chunk else 1
                end = ar_chunk[-1].get('numberInSurah', 1) if ar_chunk else 1
                
                passages.append(Passage(
                    id=f"quran:{surah}:{start}-{end}",
                    source="quran",
                    ref=f"Quran {surah}:{start}-{end}",
                    title=name,
                    text_original=ar_text,
                    text_english=en_text,
                    language="ar",
                    category="scripture",
                    subcategory="quran",
                    date_composed="610-632 CE",
                    metadata={"surah": surah}
                ))
        
        self._save(passages)
        logger.info(f"  [DONE] Quran: {len(passages)} passages")
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# BIBLE
# =============================================================================

class BibleFetcher:
    BASE = "https://bible-api.com"
    
    REFS = [
        "genesis+1:1-31", "exodus+20:1-17", "leviticus+19:1-18",
        "deuteronomy+5:1-21", "deuteronomy+6:4-9",
        "psalm+1", "psalm+23", "proverbs+1:1-19", "proverbs+3:1-18",
        "ecclesiastes+3:1-15", "isaiah+1:10-20", "micah+6:1-8",
        "matthew+5:1-48", "matthew+6:1-34", "matthew+7:1-29",
        "matthew+22:34-40", "mark+12:28-34", "luke+6:27-36",
        "john+13:34-35", "romans+12:1-21", "romans+13:1-14",
        "1corinthians+13:1-13", "galatians+5:16-26",
        "ephesians+4:25-32", "philippians+2:1-11",
        "colossians+3:12-17", "james+1:19-27", "james+2:1-26",
        "1peter+3:8-17", "1john+3:11-24", "1john+4:7-21",
    ]
    
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "bible"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[BIBLE] Starting...")
        
        passages = []
        
        for ref in self.REFS:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            data = self.client.get(f"{self.BASE}/{ref}")
            
            if not data:
                continue
            
            text = data.get('text', '')
            if not text:
                continue
            
            display_ref = ref.replace('+', ' ')
            
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
                metadata={"translation": data.get('translation_name', 'WEB')}
            ))
        
        self._save(passages)
        logger.info(f"  [DONE] Bible: {len(passages)} passages")
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# EMBEDDED SAMPLES
# =============================================================================

class EmbeddedFetcher:
    def __init__(self, client: HTTPClient, config: FetcherConfig):
        self.config = config
        self.output_dir = Path(config.output_dir) / "embedded"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[EMBEDDED] Loading samples...")
        
        passages = []
        
        # Chinese classics
        chinese = [
            ("Analects 4:15", "The Master's way is loyalty and reciprocity, that is all."),
            ("Analects 12:2", "Do not do to others what you would not wish done to yourself."),
            ("Analects 15:24", "Is there one word for life? Reciprocity."),
            ("Mencius 7A:4", "All things are complete in us."),
            ("Tao Te Ching 63", "Respond to injury with virtue."),
        ]
        for ref, text in chinese:
            passages.append(Passage(
                id=f"chinese:{ref.replace(' ', '_')}", source="chinese",
                ref=ref, title=ref.split()[0], text_original=text, text_english=text,
                language="zh", category="philosophy", subcategory="confucian",
                date_composed="500 BCE", metadata={"embedded": True}
            ))
        
        # Greek/Roman
        greek = [
            ("Aristotle NE 1094a", "Every art aims at some good."),
            ("Aristotle NE 1106b", "Virtue is a mean between extremes."),
            ("Plato Crito 49b", "Never retaliate evil for evil."),
            ("Epictetus Ench. 1", "Some things are in our control, others not."),
            ("Marcus Aurelius Med. 2.1", "Wrong arises from ignorance."),
            ("Seneca Letters 95", "Treat others as you wish to be treated."),
        ]
        for ref, text in greek:
            passages.append(Passage(
                id=f"greek:{ref.replace(' ', '_')}", source="greek_roman",
                ref=ref, title=ref.split()[0], text_original=text, text_english=text,
                language="grc", category="philosophy", subcategory="ethics",
                date_composed="Ancient", metadata={"embedded": True}
            ))
        
        # Roman law
        roman = [
            ("Digest 1.1.1", "Law is the art of the good and fair."),
            ("Digest 1.1.10", "Justice is rendering each their due."),
            ("Digest 1.1.10.1", "Live honestly, harm none, give each their due."),
            ("Digest 50.17.185", "No obligation to the impossible."),
        ]
        for ref, text in roman:
            passages.append(Passage(
                id=f"roman:{ref.replace(' ', '_')}", source="roman_law",
                ref=ref, title="Digest", text_original=text, text_english=text,
                language="la", category="legal", subcategory="roman",
                date_composed="533 CE", metadata={"embedded": True}
            ))
        
        self._save(passages)
        logger.info(f"  [DONE] Embedded: {len(passages)} samples")
        return passages
    
    def _save(self, passages: List[Passage]):
        out = self.output_dir / "passages.json"
        out.write_text(json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False), encoding='utf-8')


# =============================================================================
# COMBINER
# =============================================================================

class Combiner:
    def __init__(self, config: FetcherConfig):
        self.output_dir = Path(config.output_dir)
    
    def combine(self) -> Dict:
        all_p = []
        stats = {"sources": {}}
        
        for d in self.output_dir.iterdir():
            if d.is_dir() and not d.name.startswith('.'):
                f = d / "passages.json"
                if f.exists():
                    data = json.loads(f.read_text(encoding='utf-8'))
                    all_p.extend(data)
                    stats["sources"][d.name] = len(data)
        
        stats["total"] = len(all_p)
        
        (self.output_dir / "combined_corpus.json").write_text(
            json.dumps(all_p, indent=2, ensure_ascii=False), encoding='utf-8')
        (self.output_dir / "corpus_stats.json").write_text(
            json.dumps(stats, indent=2), encoding='utf-8')
        
        logger.info(f"\n=== FINAL: {stats['total']} passages ===")
        for s, c in sorted(stats["sources"].items()):
            logger.info(f"  {s}: {c}")
        
        return stats


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Verbose Ethics Corpus Fetcher")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--sefaria", action="store_true")
    parser.add_argument("--quran", action="store_true")
    parser.add_argument("--hadith", action="store_true")
    parser.add_argument("--bible", action="store_true")
    parser.add_argument("--gita", action="store_true")
    parser.add_argument("--buddhist", action="store_true")
    parser.add_argument("--courtlistener", action="store_true")
    parser.add_argument("--embedded", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", default="./corpus")
    parser.add_argument("--quiet", action="store_true", help="Less verbose logging")
    
    args = parser.parse_args()
    
    if not any([args.all, args.sefaria, args.quran, args.hadith, args.bible,
                args.gita, args.buddhist, args.courtlistener, args.embedded]):
        parser.print_help()
        return
    
    config = FetcherConfig(
        output_dir=args.output,
        limit_per_source=args.limit,
        verbose=not args.quiet,
    )
    
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    client = HTTPClient(config)
    
    print("=" * 60)
    print("VERBOSE ETHICS CORPUS FETCHER")
    print("=" * 60)
    
    fetchers = []
    if args.all or args.sefaria: fetchers.append(SefariaFetcher(client, config))
    if args.all or args.quran: fetchers.append(QuranFetcher(client, config))
    if args.all or args.hadith: fetchers.append(HadithFetcher(client, config))
    if args.all or args.bible: fetchers.append(BibleFetcher(client, config))
    if args.all or args.gita: fetchers.append(GitaFetcher(client, config))
    if args.all or args.buddhist: fetchers.append(SuttaCentralFetcher(client, config))
    if args.all or args.courtlistener: fetchers.append(CourtListenerFetcher(client, config))
    if args.all or args.embedded: fetchers.append(EmbeddedFetcher(client, config))
    
    for f in fetchers:
        try:
            f.fetch_all()
        except Exception as e:
            logger.error(f"{type(f).__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    Combiner(config).combine()
    
    print("\n" + "=" * 60)
    print("[COMPLETE]")
    print("=" * 60)


if __name__ == "__main__":
    main()
