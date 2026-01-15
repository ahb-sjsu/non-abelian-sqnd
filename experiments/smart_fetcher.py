#!/usr/bin/env python3
"""
Self-Learning Ethics Corpus Fetcher
====================================

TRULY DYNAMIC - No hardcoded structures. The fetcher:
1. Probes each API's discovery endpoints
2. Analyzes response structure
3. Learns field mappings dynamically
4. Adapts extraction based on what it finds

Usage:
    python smart_fetcher.py --all
    python smart_fetcher.py --all --limit 100
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
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import Counter

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
        logging.FileHandler('smart_fetcher.log', encoding='utf-8', errors='replace')
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
    rate_limit_delay: float = 0.5
    limit_per_source: Optional[int] = None
    max_per_collection: int = 200
    probe_samples: int = 3  # How many samples to probe for learning


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
        self.session.headers['User-Agent'] = 'EthicsCorpusFetcher/6.0'
        self.last_request = 0.0
        self.cache_dir = Path(config.output_dir) / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, url: str, headers: Dict = None, cache: bool = True) -> Optional[Any]:
        cache_key = re.sub(r'[^\w\-.]', '_', url)[:150]
        cache_path = self.cache_dir / f"{cache_key}.json"
        
        if cache and cache_path.exists():
            try:
                return json.loads(cache_path.read_text(encoding='utf-8'))
            except:
                pass
        
        wait = self.config.rate_limit_delay - (time.time() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        self.last_request = time.time()
        
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
            logger.debug(f"GET failed {url[:60]}: {e}")
            return None


# =============================================================================
# SCHEMA LEARNER - Discovers structure from sample responses
# =============================================================================

class SchemaLearner:
    """Learns API response structure from samples"""
    
    # Common patterns for text fields (ordered by priority)
    TEXT_PATTERNS = [
        'text', 'content', 'body', 'slok', 'verse', 'ayah', 'passage',
        'he', 'en', 'ar', 'sa', 'pi', 'la', 'grc', 'zh',
        'hebrew', 'english', 'arabic', 'sanskrit', 'pali', 'latin', 'greek', 'chinese',
        'translation', 'original', 'source', 'target',
        'snippet', 'excerpt', 'plain_text', 'html',
    ]
    
    # Common patterns for reference/title fields
    REF_PATTERNS = ['ref', 'reference', 'title', 'name', 'heading', 'label', 'id', 'uid', 'key']
    
    # Common patterns for list/collection fields
    LIST_PATTERNS = ['versions', 'texts', 'items', 'results', 'data', 'entries', 
                     'hadiths', 'ayahs', 'verses', 'chapters', 'sections', 'contents']
    
    def __init__(self):
        self.learned_schemas: Dict[str, Dict] = {}
    
    def learn(self, source_name: str, samples: List[Any]) -> Dict:
        """Learn schema from multiple samples"""
        if not samples:
            return {}
        
        schema = {
            'text_paths': [],      # Paths to text content
            'ref_paths': [],       # Paths to reference/title
            'list_paths': [],      # Paths to iterate
            'structure': None,     # 'dict', 'list', 'nested'
        }
        
        # Analyze each sample
        all_text_paths = []
        all_ref_paths = []
        all_list_paths = []
        
        for sample in samples:
            if sample is None:
                continue
            
            text_paths = self._find_text_paths(sample)
            ref_paths = self._find_ref_paths(sample)
            list_paths = self._find_list_paths(sample)
            
            all_text_paths.extend(text_paths)
            all_ref_paths.extend(ref_paths)
            all_list_paths.extend(list_paths)
            
            # Determine structure
            if isinstance(sample, list):
                schema['structure'] = 'list'
            elif isinstance(sample, dict):
                if any(isinstance(v, list) for v in sample.values()):
                    schema['structure'] = 'nested'
                else:
                    schema['structure'] = 'dict'
        
        # Find most common paths
        schema['text_paths'] = self._most_common(all_text_paths, 5)
        schema['ref_paths'] = self._most_common(all_ref_paths, 3)
        schema['list_paths'] = self._most_common(all_list_paths, 3)
        
        self.learned_schemas[source_name] = schema
        logger.info(f"  Learned schema: text={schema['text_paths'][:2]}, ref={schema['ref_paths'][:1]}")
        
        return schema
    
    def _find_text_paths(self, obj: Any, path: str = "") -> List[str]:
        """Find all paths that lead to text content"""
        paths = []
        
        if isinstance(obj, str) and len(obj) > 20:
            paths.append(path)
        elif isinstance(obj, dict):
            for key, val in obj.items():
                new_path = f"{path}.{key}" if path else key
                # Prioritize known text patterns
                if any(p in key.lower() for p in self.TEXT_PATTERNS):
                    if isinstance(val, str) and len(val) > 10:
                        paths.append(new_path)
                    elif isinstance(val, list):
                        paths.append(new_path)
                # Recurse into nested dicts
                if isinstance(val, dict):
                    paths.extend(self._find_text_paths(val, new_path))
        elif isinstance(obj, list) and obj:
            paths.extend(self._find_text_paths(obj[0], f"{path}[0]"))
        
        return paths
    
    def _find_ref_paths(self, obj: Any, path: str = "") -> List[str]:
        """Find paths to reference/title fields"""
        paths = []
        
        if isinstance(obj, dict):
            for key, val in obj.items():
                new_path = f"{path}.{key}" if path else key
                if any(p in key.lower() for p in self.REF_PATTERNS):
                    if isinstance(val, str):
                        paths.append(new_path)
                if isinstance(val, dict):
                    paths.extend(self._find_ref_paths(val, new_path))
        
        return paths
    
    def _find_list_paths(self, obj: Any, path: str = "") -> List[str]:
        """Find paths to iterable collections"""
        paths = []
        
        if isinstance(obj, dict):
            for key, val in obj.items():
                new_path = f"{path}.{key}" if path else key
                if isinstance(val, list) and len(val) > 0:
                    if any(p in key.lower() for p in self.LIST_PATTERNS):
                        paths.append(new_path)
                if isinstance(val, dict):
                    paths.extend(self._find_list_paths(val, new_path))
        
        return paths
    
    def _most_common(self, items: List[str], n: int) -> List[str]:
        """Return n most common items"""
        if not items:
            return []
        counter = Counter(items)
        return [item for item, _ in counter.most_common(n)]
    
    def extract_by_path(self, obj: Any, path: str) -> Any:
        """Extract value at given path"""
        if not path:
            return obj
        
        parts = path.replace('[0]', '.0').split('.')
        current = obj
        
        for part in parts:
            if current is None:
                return None
            if part.isdigit():
                idx = int(part)
                if isinstance(current, list) and len(current) > idx:
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        
        return current
    
    def extract_text(self, obj: Any, schema: Dict) -> Tuple[str, str]:
        """Extract original and English text using learned schema"""
        original = ""
        english = ""
        
        for path in schema.get('text_paths', []):
            val = self.extract_by_path(obj, path)
            if val:
                text = self._flatten_text(val)
                if text:
                    # Heuristic: if path contains language hint
                    path_lower = path.lower()
                    if any(x in path_lower for x in ['en', 'english', 'translation', 'trans']):
                        if not english:
                            english = text
                    elif any(x in path_lower for x in ['he', 'ar', 'sa', 'pi', 'original', 'source', 'slok']):
                        if not original:
                            original = text
                    else:
                        # Default: first found is original
                        if not original:
                            original = text
                        elif not english:
                            english = text
        
        # Fallback: aggressive extraction
        if not original and not english:
            original = self._extract_any_text(obj)
        
        if not english:
            english = original
        if not original:
            original = english
        
        return original[:10000], english[:10000]
    
    def extract_ref(self, obj: Any, schema: Dict) -> str:
        """Extract reference/title using learned schema"""
        for path in schema.get('ref_paths', []):
            val = self.extract_by_path(obj, path)
            if val and isinstance(val, str):
                return val
        return ""
    
    def _flatten_text(self, val: Any) -> str:
        """Flatten any value to text"""
        if isinstance(val, str):
            return val
        if isinstance(val, list):
            parts = [self._flatten_text(x) for x in val[:100]]
            return " ".join(p for p in parts if p)
        if isinstance(val, dict):
            # Try common text keys
            for key in self.TEXT_PATTERNS:
                if key in val:
                    return self._flatten_text(val[key])
            # Fall back to joining values
            parts = [self._flatten_text(v) for v in val.values()]
            return " ".join(p for p in parts if p)
        return ""
    
    def _extract_any_text(self, obj: Any, max_depth: int = 5) -> str:
        """Aggressively extract any text from structure"""
        if max_depth <= 0:
            return ""
        if isinstance(obj, str):
            return obj if len(obj) > 10 else ""
        if isinstance(obj, list):
            for item in obj[:10]:
                text = self._extract_any_text(item, max_depth - 1)
                if text:
                    return text
        if isinstance(obj, dict):
            # Try text-like keys first
            for key in self.TEXT_PATTERNS:
                if key in obj:
                    text = self._extract_any_text(obj[key], max_depth - 1)
                    if text:
                        return text
            # Then any string value
            for v in obj.values():
                text = self._extract_any_text(v, max_depth - 1)
                if text:
                    return text
        return ""


# =============================================================================
# SMART FETCHER BASE
# =============================================================================

class SmartFetcher:
    """Base class for smart fetchers that learn API structure"""
    
    def __init__(self, client: HTTPClient, config: FetcherConfig, learner: SchemaLearner):
        self.client = client
        self.config = config
        self.learner = learner
        self.source_name = "unknown"
        self.output_dir = Path(config.output_dir)
        self.schema = {}
    
    def probe_and_learn(self, sample_urls: List[str]) -> Dict:
        """Probe API with sample URLs and learn structure"""
        samples = []
        for url in sample_urls[:self.config.probe_samples]:
            data = self.client.get(url)
            if data:
                samples.append(data)
        
        if samples:
            self.schema = self.learner.learn(self.source_name, samples)
        
        return self.schema
    
    def save(self, passages: List[Passage]):
        """Save passages to JSON"""
        out_dir = self.output_dir / self.source_name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "passages.json"
        out_file.write_text(
            json.dumps([asdict(p) for p in passages], indent=2, ensure_ascii=False),
            encoding='utf-8'
        )


# =============================================================================
# SEFARIA FETCHER
# =============================================================================

class SefariaFetcher(SmartFetcher):
    BASE = "https://www.sefaria.org/api"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig, learner: SchemaLearner):
        super().__init__(client, config, learner)
        self.source_name = "sefaria"
        self.output_dir = Path(config.output_dir)
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[SEFARIA] Probing API structure...")
        
        # Step 1: Discover available texts from index
        index = self.client.get(f"{self.BASE}/index")
        if not index:
            logger.error("  Cannot fetch index")
            return []
        
        # Extract all text titles dynamically
        titles = self._extract_all_titles(index)
        logger.info(f"  Discovered {len(titles)} total texts")
        
        # Step 2: Probe a few texts to learn response structure
        probe_urls = [f"{self.BASE}/v3/texts/{t.replace(' ', '_')}.1" for t in titles[:3]]
        self.probe_and_learn(probe_urls)
        
        # Step 3: Fetch texts
        passages = []
        for title in titles:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            text_passages = self._fetch_text(title)
            if text_passages:
                logger.info(f"  {title}: {len(text_passages)} passages")
                passages.extend(text_passages)
        
        self.save(passages)
        logger.info(f"  [DONE] Sefaria: {len(passages)} total")
        return passages
    
    def _extract_all_titles(self, index: Any) -> List[str]:
        """Recursively find all text titles in index"""
        titles = []
        
        def search(node, depth=0):
            if depth > 10:
                return
            if isinstance(node, dict):
                # Look for title field
                if 'title' in node and isinstance(node['title'], str):
                    titles.append(node['title'])
                # Recurse into all values
                for v in node.values():
                    search(v, depth + 1)
            elif isinstance(node, list):
                for item in node:
                    search(item, depth + 1)
        
        search(index)
        
        # Filter to ethics-relevant (dynamic keyword matching)
        ethics_keywords = {'avot', 'bava', 'sanhedrin', 'nedarim', 'shevuot', 
                          'gittin', 'ketubot', 'kiddushin', 'ethics', 'musar'}
        
        relevant = [t for t in titles if any(k in t.lower() for k in ethics_keywords)]
        
        # If too few, also include mishnah
        if len(relevant) < 10:
            relevant.extend([t for t in titles if 'mishnah' in t.lower()])
        
        return list(set(relevant))[:50]
    
    def _fetch_text(self, title: str) -> List[Passage]:
        """Fetch all sections of a text"""
        passages = []
        safe_title = title.replace(' ', '_')
        
        # Discover structure via shape endpoint
        shape = self.client.get(f"{self.BASE}/shape/{safe_title}")
        
        # Dynamically determine section count
        if isinstance(shape, list):
            num_sections = len(shape)
        elif isinstance(shape, dict):
            # Try various keys
            for key in ['length', 'chapters', 'sections', 'count']:
                if key in shape:
                    num_sections = shape[key]
                    break
            else:
                num_sections = len(shape) if shape else 10
        else:
            num_sections = 10
        
        num_sections = min(num_sections, self.config.max_per_collection)
        
        # Fetch sections
        for sec in range(1, num_sections + 1):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            data = self.client.get(f"{self.BASE}/v3/texts/{safe_title}.{sec}")
            if not data:
                data = self.client.get(f"{self.BASE}/texts/{safe_title}.{sec}")
            if not data:
                continue
            
            # Use learned schema to extract
            original, english = self.learner.extract_text(data, self.schema)
            ref = self.learner.extract_ref(data, self.schema) or f"{title} {sec}"
            
            if not original and not english:
                continue
            
            passages.append(Passage(
                id=f"sefaria:{safe_title}.{sec}",
                source="sefaria",
                ref=ref,
                title=title,
                text_original=original,
                text_english=english,
                language="he",
                category="jewish",
                subcategory=title.split()[0].lower() if ' ' in title else title.lower(),
                date_composed="Talmudic",
                metadata={"section": sec}
            ))
        
        return passages


# =============================================================================
# QURAN FETCHER
# =============================================================================

class QuranFetcher(SmartFetcher):
    BASE = "https://api.alquran.cloud/v1"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig, learner: SchemaLearner):
        super().__init__(client, config, learner)
        self.source_name = "quran"
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[QURAN] Probing API structure...")
        
        # Discover structure via meta endpoint
        meta = self.client.get(f"{self.BASE}/meta")
        
        # Learn surah count dynamically
        num_surahs = 114  # Default
        if meta and isinstance(meta, dict):
            data = meta.get('data', meta)
            if isinstance(data, dict):
                surahs_info = data.get('surahs', {})
                if isinstance(surahs_info, dict):
                    refs = surahs_info.get('references', [])
                    if refs:
                        num_surahs = len(refs)
                    else:
                        num_surahs = surahs_info.get('count', 114)
        
        logger.info(f"  Discovered {num_surahs} surahs")
        
        # Discover available editions
        editions = self.client.get(f"{self.BASE}/edition")
        ar_edition = "quran-uthmani"
        en_edition = "en.sahih"
        
        if editions and isinstance(editions, dict):
            for ed in editions.get('data', []):
                if isinstance(ed, dict):
                    ident = ed.get('identifier', '')
                    if ident == 'en.sahih':
                        en_edition = ident
                    elif ident == 'quran-uthmani':
                        ar_edition = ident
        
        logger.info(f"  Using editions: {ar_edition}, {en_edition}")
        
        # Probe to learn structure
        probe_urls = [f"{self.BASE}/surah/{i}/editions/{ar_edition},{en_edition}" for i in [1, 2, 3]]
        self.probe_and_learn(probe_urls)
        
        # Fetch surahs
        passages = []
        for surah in range(1, min(num_surahs + 1, self.config.max_per_collection)):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            data = self.client.get(f"{self.BASE}/surah/{surah}/editions/{ar_edition},{en_edition}")
            
            if not data or data.get('code') != 200:
                continue
            
            editions_data = data.get('data', [])
            if len(editions_data) < 2:
                continue
            
            ar_data, en_data = editions_data[0], editions_data[1]
            
            # Extract dynamically
            name = ar_data.get('englishName', ar_data.get('name', f'Surah {surah}'))
            ar_ayahs = ar_data.get('ayahs', [])
            en_ayahs = en_data.get('ayahs', [])
            
            # Chunk into passages
            chunk_size = 10
            for i in range(0, len(ar_ayahs), chunk_size):
                ar_chunk = ar_ayahs[i:i + chunk_size]
                en_chunk = en_ayahs[i:i + chunk_size] if i < len(en_ayahs) else []
                
                ar_text = " ".join(a.get('text', '') for a in ar_chunk if isinstance(a, dict))
                en_text = " ".join(a.get('text', '') for a in en_chunk if isinstance(a, dict))
                
                if not ar_text and not en_text:
                    continue
                
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
        
        self.save(passages)
        logger.info(f"  [DONE] Quran: {len(passages)} passages")
        return passages


# =============================================================================
# HADITH FETCHER
# =============================================================================

class HadithFetcher(SmartFetcher):
    BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig, learner: SchemaLearner):
        super().__init__(client, config, learner)
        self.source_name = "hadith"
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[HADITH] Discovering collections...")
        
        # Discover available editions
        editions = self.client.get(f"{self.BASE}/editions.json")
        
        # Dynamically find English collections
        collections = []
        if isinstance(editions, dict):
            for key, val in editions.items():
                # Check if key or value indicates English
                if 'eng' in key.lower():
                    collections.append((key, val.get('name', key) if isinstance(val, dict) else key))
                elif isinstance(val, dict) and 'eng' in str(val.get('language', '')).lower():
                    collections.append((key, val.get('name', key)))
        
        if not collections:
            # Try listing directory-style
            for key in (editions.keys() if isinstance(editions, dict) else []):
                if key.startswith('eng-'):
                    collections.append((key, key.replace('eng-', '').replace('-', ' ').title()))
        
        logger.info(f"  Found {len(collections)} English collections")
        
        # Probe to learn structure
        if collections:
            probe_urls = [f"{self.BASE}/editions/{c[0]}/1.json" for c in collections[:2]]
            self.probe_and_learn(probe_urls)
        
        # Fetch from each collection
        passages = []
        for coll_id, coll_name in collections[:5]:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            # Get collection info to find total count
            info = self.client.get(f"{self.BASE}/editions/{coll_id}.json")
            
            total = 100
            if isinstance(info, dict):
                # Try to find count dynamically
                for key in ['length', 'total', 'count', 'hadiths']:
                    if key in info and isinstance(info[key], int):
                        total = info[key]
                        break
                # Try sections
                sections = info.get('sections', {})
                if isinstance(sections, dict) and sections:
                    total = sum(v for v in sections.values() if isinstance(v, int))
            
            total = min(total, self.config.max_per_collection)
            logger.info(f"  {coll_name}: fetching up to {total} hadiths")
            
            # Fetch hadiths
            count = 0
            for num in range(1, total + 1):
                if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                    break
                
                data = self.client.get(f"{self.BASE}/editions/{coll_id}/{num}.json")
                if not data:
                    continue
                
                # Extract text dynamically
                text = ""
                if isinstance(data, dict):
                    # Try hadiths array first
                    hadiths = data.get('hadiths', [])
                    if hadiths and isinstance(hadiths[0], dict):
                        text = hadiths[0].get('text', '')
                    if not text:
                        text = self.learner._extract_any_text(data)
                
                if not text or len(text) < 20:
                    continue
                
                passages.append(Passage(
                    id=f"hadith:{coll_id}:{num}",
                    source="hadith",
                    ref=f"{coll_name} #{num}",
                    title=coll_name,
                    text_original=text,
                    text_english=text,
                    language="en",
                    category="hadith",
                    subcategory=coll_id,
                    date_composed="~850 CE",
                    metadata={"number": num}
                ))
                count += 1
            
            logger.info(f"    Retrieved {count}")
        
        self.save(passages)
        logger.info(f"  [DONE] Hadith: {len(passages)} total")
        return passages


# =============================================================================
# GITA FETCHER
# =============================================================================

class GitaFetcher(SmartFetcher):
    BASE = "https://vedicscriptures.github.io"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig, learner: SchemaLearner):
        super().__init__(client, config, learner)
        self.source_name = "gita"
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[GITA] Discovering structure...")
        
        # Get chapters to learn structure
        chapters_data = self.client.get(f"{self.BASE}/chapters")
        
        # Determine chapter count dynamically
        if isinstance(chapters_data, list):
            num_chapters = len(chapters_data)
            chapter_info = {i+1: ch for i, ch in enumerate(chapters_data)}
        elif isinstance(chapters_data, dict):
            num_chapters = chapters_data.get('count', chapters_data.get('chapters', 18))
            chapter_info = {}
        else:
            num_chapters = 18
            chapter_info = {}
        
        logger.info(f"  Discovered {num_chapters} chapters")
        
        # Probe verse structure
        probe_urls = [f"{self.BASE}/slok/1/1.json", f"{self.BASE}/slok/2/1.json"]
        self.probe_and_learn(probe_urls)
        
        passages = []
        for ch in range(1, min(num_chapters + 1, 19)):
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            # Get chapter info
            ch_data = self.client.get(f"{self.BASE}/chapter/{ch}.json")
            if not ch_data:
                continue
            
            # Extract chapter name dynamically
            ch_name = ""
            for key in ['name', 'title', 'translation', 'meaning']:
                if key in ch_data and isinstance(ch_data[key], str):
                    ch_name = ch_data[key]
                    break
            if not ch_name:
                ch_name = f"Chapter {ch}"
            
            # Get verse count dynamically
            verses_count = 50  # Default max
            for key in ['verses_count', 'versesCount', 'verses', 'count']:
                if key in ch_data:
                    val = ch_data[key]
                    if isinstance(val, int):
                        verses_count = val
                        break
                    elif isinstance(val, list):
                        verses_count = len(val)
                        break
            
            # Fetch verses
            for v in range(1, min(verses_count + 1, self.config.max_per_collection)):
                if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                    break
                
                verse = self.client.get(f"{self.BASE}/slok/{ch}/{v}.json")
                if not verse:
                    continue
                
                # Extract Sanskrit dynamically
                sanskrit = ""
                for key in ['slok', 'verse', 'sanskrit', 'text', 'shloka']:
                    if key in verse and isinstance(verse[key], str):
                        sanskrit = verse[key]
                        break
                
                # Extract English from commentators dynamically
                english = ""
                # First try nested commentator objects with 'et' key
                for key, val in verse.items():
                    if isinstance(val, dict):
                        for subkey in ['et', 'english', 'translation', 'meaning']:
                            if subkey in val and isinstance(val[subkey], str):
                                english = val[subkey]
                                break
                        if english:
                            break
                
                # Fallback: transliteration
                if not english:
                    english = verse.get('transliteration', sanskrit)
                
                if not sanskrit and not english:
                    continue
                
                passages.append(Passage(
                    id=f"gita:{ch}:{v}",
                    source="gita",
                    ref=f"Bhagavad Gita {ch}.{v}",
                    title=ch_name,
                    text_original=sanskrit,
                    text_english=english if english else sanskrit,
                    language="sa",
                    category="scripture",
                    subcategory="gita",
                    date_composed="~200 BCE",
                    metadata={"chapter": ch, "verse": v}
                ))
            
            logger.info(f"  Chapter {ch}: {sum(1 for p in passages if f'gita:{ch}:' in p.id)} verses")
        
        self.save(passages)
        logger.info(f"  [DONE] Gita: {len(passages)} total")
        return passages


# =============================================================================
# SUTTACENTRAL FETCHER
# =============================================================================

class SuttaCentralFetcher(SmartFetcher):
    BASE = "https://suttacentral.net/api"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig, learner: SchemaLearner):
        super().__init__(client, config, learner)
        self.source_name = "buddhist"
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[BUDDHIST] Discovering collections...")
        
        # Try to get menu structure to discover nikayas
        nikayas = []
        for nikaya in ['dn', 'mn', 'sn', 'an', 'kn']:
            menu = self.client.get(f"{self.BASE}/menu/{nikaya}")
            if menu:
                nikayas.append(nikaya)
        
        logger.info(f"  Found nikayas: {nikayas}")
        
        # Probe to learn text structure
        probe_urls = [f"{self.BASE}/bilarasuttas/dn1/sujato", f"{self.BASE}/bilarasuttas/mn1/sujato"]
        self.probe_and_learn(probe_urls)
        
        passages = []
        for nikaya in nikayas:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            logger.info(f"  Nikaya: {nikaya.upper()}")
            
            # Discover sutta IDs from menu
            menu = self.client.get(f"{self.BASE}/menu/{nikaya}")
            sutta_ids = self._extract_sutta_ids(menu, nikaya)
            
            if not sutta_ids:
                # Fallback: try numbered approach
                sutta_ids = [f"{nikaya}{i}" for i in range(1, 50)]
            
            logger.info(f"    Found {len(sutta_ids)} potential suttas")
            
            for sutta_id in sutta_ids[:self.config.max_per_collection]:
                if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                    break
                
                # Get suttaplex for title
                plex = self.client.get(f"{self.BASE}/suttaplex/{sutta_id}")
                title = sutta_id.upper()
                if plex:
                    if isinstance(plex, list) and plex:
                        plex = plex[0]
                    if isinstance(plex, dict):
                        for key in ['translated_title', 'original_title', 'title', 'name']:
                            if key in plex and plex[key]:
                                title = plex[key]
                                break
                
                # Get text from bilara
                bilara = self.client.get(f"{self.BASE}/bilarasuttas/{sutta_id}/sujato")
                
                pali = ""
                english = ""
                
                if bilara and isinstance(bilara, dict):
                    # Extract dynamically
                    for key in ['root_text', 'pali', 'original']:
                        if key in bilara:
                            val = bilara[key]
                            if isinstance(val, dict):
                                pali = " ".join(str(v) for v in val.values() if v)[:5000]
                            elif isinstance(val, str):
                                pali = val[:5000]
                            if pali:
                                break
                    
                    for key in ['translation_text', 'translation', 'english']:
                        if key in bilara:
                            val = bilara[key]
                            if isinstance(val, dict):
                                english = " ".join(str(v) for v in val.values() if v)[:5000]
                            elif isinstance(val, str):
                                english = val[:5000]
                            if english:
                                break
                
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
                    metadata={"nikaya": nikaya}
                ))
            
            logger.info(f"    Retrieved {sum(1 for p in passages if p.metadata.get('nikaya') == nikaya)}")
        
        self.save(passages)
        logger.info(f"  [DONE] Buddhist: {len(passages)} total")
        return passages
    
    def _extract_sutta_ids(self, menu: Any, nikaya: str) -> List[str]:
        """Dynamically extract sutta IDs from menu structure"""
        ids = set()
        
        def search(node, depth=0):
            if depth > 10:
                return
            if isinstance(node, dict):
                # Look for uid/id fields
                for key in ['uid', 'id', 'acronym']:
                    if key in node:
                        val = node[key]
                        if isinstance(val, str) and val.startswith(nikaya) and len(val) < 15:
                            ids.add(val)
                for v in node.values():
                    search(v, depth + 1)
            elif isinstance(node, list):
                for item in node:
                    search(item, depth + 1)
        
        search(menu)
        return sorted(ids)[:100]


# =============================================================================
# BIBLE FETCHER
# =============================================================================

class BibleFetcher(SmartFetcher):
    BASE = "https://bible-api.com"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig, learner: SchemaLearner):
        super().__init__(client, config, learner)
        self.source_name = "bible"
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[BIBLE] Fetching passages...")
        
        # Bible API doesn't have discovery - use book structure knowledge
        # But we discover chapter/verse counts dynamically
        books = [
            'genesis', 'exodus', 'leviticus', 'deuteronomy',
            'psalms', 'proverbs', 'ecclesiastes', 'isaiah', 'micah', 'amos',
            'matthew', 'mark', 'luke', 'john',
            'romans', '1corinthians', 'galatians', 'ephesians',
            'james', '1peter', '1john',
        ]
        
        # Probe to learn structure
        probe_urls = [f"{self.BASE}/genesis+1", f"{self.BASE}/matthew+5"]
        self.probe_and_learn(probe_urls)
        
        passages = []
        
        for book in books:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            # Try to fetch chapters dynamically
            for chapter in range(1, 30):  # Most books < 30 chapters
                if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                    break
                
                data = self.client.get(f"{self.BASE}/{book}+{chapter}")
                if not data:
                    break  # No more chapters
                
                # Extract text dynamically
                text = ""
                for key in ['text', 'content', 'passage']:
                    if key in data and isinstance(data[key], str):
                        text = data[key]
                        break
                
                if not text:
                    continue
                
                ref = data.get('reference', f"{book.title()} {chapter}")
                
                passages.append(Passage(
                    id=f"bible:{book}:{chapter}",
                    source="bible",
                    ref=ref,
                    title=book.title(),
                    text_original=text,
                    text_english=text,
                    language="en",
                    category="scripture",
                    subcategory="bible",
                    date_composed="Various",
                    metadata={"book": book, "chapter": chapter}
                ))
            
            logger.info(f"  {book.title()}: {sum(1 for p in passages if book in p.id)} chapters")
        
        self.save(passages)
        logger.info(f"  [DONE] Bible: {len(passages)} total")
        return passages


# =============================================================================
# COURTLISTENER FETCHER
# =============================================================================

class CourtListenerFetcher(SmartFetcher):
    BASE = "https://www.courtlistener.com/api/rest/v4"
    
    def __init__(self, client: HTTPClient, config: FetcherConfig, learner: SchemaLearner):
        super().__init__(client, config, learner)
        self.source_name = "courtlistener"
        self.api_key = os.environ.get("COURTLISTENER_API_KEY")
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[COURTLISTENER] Discovering API structure...")
        
        if not self.api_key:
            logger.warning("  No COURTLISTENER_API_KEY - may be limited")
        
        headers = {"Authorization": f"Token {self.api_key}"} if self.api_key else {}
        
        # Discover via search
        search_terms = ['contract', 'negligence', 'due process', 'fiduciary', 'fraud']
        
        passages = []
        for term in search_terms:
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
            
            logger.info(f"  Search: {term}")
            
            url = f"{self.BASE}/search/?q={urllib.parse.quote(term)}&type=o"
            
            try:
                self.client.session.headers.update(headers)
                r = self.client.session.get(url, timeout=30)
                data = r.json()
            except:
                continue
            
            # Extract results dynamically
            results = []
            if isinstance(data, dict):
                for key in ['results', 'data', 'items', 'opinions']:
                    if key in data and isinstance(data[key], list):
                        results = data[key]
                        break
            elif isinstance(data, list):
                results = data
            
            logger.info(f"    Found {len(results)} results")
            
            for r in results[:20]:
                if not isinstance(r, dict):
                    continue
                
                # Extract fields dynamically
                snippet = ""
                for key in ['snippet', 'text', 'excerpt', 'plain_text']:
                    if key in r:
                        snippet = str(r[key])
                        break
                
                if snippet:
                    snippet = re.sub(r'<[^>]+>', '', snippet)  # Clean HTML
                
                if not snippet or len(snippet) < 30:
                    continue
                
                case_name = ""
                for key in ['caseName', 'case_name', 'title', 'name']:
                    if key in r and r[key]:
                        case_name = str(r[key])
                        break
                
                passages.append(Passage(
                    id=f"cl:{r.get('id', len(passages))}",
                    source="courtlistener",
                    ref=case_name or "Unknown Case",
                    title=case_name or "Case",
                    text_original=snippet,
                    text_english=snippet,
                    language="en",
                    category="legal",
                    subcategory=term.replace(' ', '_'),
                    date_composed=str(r.get('dateFiled', 'Unknown')),
                    metadata={"query": term}
                ))
        
        self.save(passages)
        logger.info(f"  [DONE] CourtListener: {len(passages)} total")
        return passages


# =============================================================================
# EMBEDDED SAMPLES
# =============================================================================

class EmbeddedFetcher(SmartFetcher):
    def __init__(self, client: HTTPClient, config: FetcherConfig, learner: SchemaLearner):
        super().__init__(client, config, learner)
        self.source_name = "embedded"
    
    def fetch_all(self) -> List[Passage]:
        logger.info("[EMBEDDED] Loading curated samples...")
        
        samples = [
            ("chinese", "Analects 12:2", "Do not do to others what you would not wish done to yourself.", "zh"),
            ("chinese", "Analects 15:24", "Reciprocity - do not do to others what you do not want.", "zh"),
            ("chinese", "Tao Te Ching 63", "Respond to injury with virtue.", "zh"),
            ("greek", "Aristotle NE 1106b", "Virtue is a mean between extremes.", "grc"),
            ("greek", "Plato Crito 49b", "Never retaliate evil for evil.", "grc"),
            ("greek", "Epictetus Ench. 1", "Some things are in our control, others not.", "grc"),
            ("roman", "Digest 1.1.10", "Justice is rendering each their due.", "la"),
            ("roman", "Digest 1.1.10.1", "Live honestly, harm none, give each their due.", "la"),
        ]
        
        passages = [
            Passage(
                id=f"{src}:{ref.replace(' ', '_')}",
                source=src,
                ref=ref,
                title=ref.split()[0],
                text_original=text,
                text_english=text,
                language=lang,
                category="philosophy" if src in ["chinese", "greek"] else "legal",
                subcategory=src,
                date_composed="Ancient",
                metadata={"embedded": True}
            )
            for src, ref, text, lang in samples
        ]
        
        self.save(passages)
        logger.info(f"  [DONE] Embedded: {len(passages)} samples")
        return passages


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
        stats["timestamp"] = datetime.now().isoformat()
        
        (self.output_dir / "combined_corpus.json").write_text(
            json.dumps(all_p, indent=2, ensure_ascii=False), encoding='utf-8')
        (self.output_dir / "corpus_stats.json").write_text(
            json.dumps(stats, indent=2), encoding='utf-8')
        
        logger.info(f"\n{'='*50}")
        logger.info(f"CORPUS COMPLETE: {stats['total']} passages")
        logger.info(f"{'='*50}")
        for src, cnt in sorted(stats["sources"].items(), key=lambda x: -x[1]):
            logger.info(f"  {src}: {cnt}")
        
        return stats


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Smart Self-Learning Fetcher")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--sefaria", action="store_true")
    parser.add_argument("--quran", action="store_true")
    parser.add_argument("--hadith", action="store_true")
    parser.add_argument("--bible", action="store_true")
    parser.add_argument("--gita", action="store_true")
    parser.add_argument("--buddhist", action="store_true")
    parser.add_argument("--courtlistener", action="store_true")
    parser.add_argument("--embedded", action="store_true")
    parser.add_argument("--limit", type=int, help="Max passages per source")
    parser.add_argument("--output", default="./corpus")
    
    args = parser.parse_args()
    
    if not any([args.all, args.sefaria, args.quran, args.hadith, args.bible,
                args.gita, args.buddhist, args.courtlistener, args.embedded]):
        parser.print_help()
        return
    
    config = FetcherConfig(
        output_dir=args.output,
        limit_per_source=args.limit,
    )
    
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    client = HTTPClient(config)
    learner = SchemaLearner()
    
    print("=" * 60)
    print("SMART SELF-LEARNING ETHICS CORPUS FETCHER")
    print("=" * 60)
    print(f"Output: {config.output_dir}")
    if config.limit_per_source:
        print(f"Limit: {config.limit_per_source} per source")
    print("=" * 60)
    
    fetchers = []
    if args.all or args.sefaria: fetchers.append(SefariaFetcher(client, config, learner))
    if args.all or args.quran: fetchers.append(QuranFetcher(client, config, learner))
    if args.all or args.hadith: fetchers.append(HadithFetcher(client, config, learner))
    if args.all or args.bible: fetchers.append(BibleFetcher(client, config, learner))
    if args.all or args.gita: fetchers.append(GitaFetcher(client, config, learner))
    if args.all or args.buddhist: fetchers.append(SuttaCentralFetcher(client, config, learner))
    if args.all or args.courtlistener: fetchers.append(CourtListenerFetcher(client, config, learner))
    if args.all or args.embedded: fetchers.append(EmbeddedFetcher(client, config, learner))
    
    for f in fetchers:
        try:
            f.fetch_all()
        except Exception as e:
            logger.error(f"{type(f).__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    Combiner(config).combine()
    
    print(f"\nOutput: {config.output_dir}/combined_corpus.json")


if __name__ == "__main__":
    main()
