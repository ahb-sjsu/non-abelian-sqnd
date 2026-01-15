#!/usr/bin/env python3
"""
Comprehensive Ethics Corpus Fetcher v2
======================================

FIXED based on API testing on 2026-01-10.

Working APIs:
- Sefaria (Hebrew/Jewish) - FIXED list handling
- AlQuran Cloud (Quran)
- Hadith API (Prophetic traditions)
- Bible API (Christian scriptures)
- Bhagavad Gita API (Hindu)
- CourtListener (US Case Law) - works without auth for basic search
- SuttaCentral (Buddhist)

Embedded samples only (API issues):
- Chinese Text Project (403 without key)
- Greek/Roman (Perseus) - no live API
- Roman Law (Digest) - no live API

Usage:
    python comprehensive_fetcher_v2.py --all
    python comprehensive_fetcher_v2.py --sefaria --quran --bible
    python comprehensive_fetcher_v2.py --all --limit 100
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.parse
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("ERROR: Please install requests: pip install requests")
    sys.exit(1)

# Configure logging without emojis for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fetcher.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Passage:
    """Unified passage format across all sources"""
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
    """Configuration for fetching"""
    output_dir: str = "./corpus"
    rate_limit_delay: float = 1.0
    limit_per_source: Optional[int] = None
    resume: bool = False
    courtlistener_api_key: Optional[str] = None


# =============================================================================
# HTTP CLIENT
# =============================================================================

class RobustHTTPClient:
    """HTTP client with retry logic and rate limiting"""
    
    def __init__(self, config: FetcherConfig):
        self.config = config
        self.session = self._create_session()
        self.last_request_time = 0
        
        # Create cache directory
        self.cache_dir = Path(config.output_dir) / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': 'EthicsCorpusFetcher/2.0 (Academic Research)'
        })
        
        return session
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.rate_limit_delay:
            time.sleep(self.config.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL"""
        safe_name = urllib.parse.quote(url, safe='')[:200]
        return self.cache_dir / f"{safe_name}.json"
    
    def get(self, url: str, headers: Dict = None, use_cache: bool = True) -> Optional[Any]:
        """GET request with caching and rate limiting"""
        
        # Check cache
        cache_path = self._get_cache_path(url)
        if use_cache and cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Rate limit
        self._rate_limit()
        
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache response
            if use_cache:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
            
            return data
            
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed: {url} - {e}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error for {url}: {e}")
            return None


# =============================================================================
# SEFARIA FETCHER (FIXED)
# =============================================================================

class SefariaFetcher:
    """
    Fetches from Sefaria API - Hebrew/Jewish texts
    
    FIXED: Handle list responses from index/shape endpoints
    """
    
    BASE_URL = "https://www.sefaria.org/api"
    
    # SQND-relevant texts
    TEXTS_TO_FETCH = {
        "ethics": [
            "Pirkei_Avot",           # Ethics of the Fathers
            "Derech_Eretz_Rabbah",   # Major ethical conduct
            "Derech_Eretz_Zuta",     # Minor ethical conduct
        ],
        "civil_law": [
            "Mishnah_Bava_Kamma",    # Damages/torts
            "Mishnah_Bava_Metzia",   # Found objects, employment
            "Mishnah_Bava_Batra",    # Property, inheritance
        ],
        "oaths_vows": [
            "Mishnah_Nedarim",       # Vows
            "Mishnah_Shevuot",       # Oaths
        ],
        "family": [
            "Mishnah_Kiddushin",     # Marriage
            "Mishnah_Gittin",        # Divorce
            "Mishnah_Ketubot",       # Marriage contracts
        ],
    }
    
    def __init__(self, client: RobustHTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "sefaria"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        """Fetch all SQND-relevant Sefaria texts"""
        passages = []
        
        logger.info("[SEFARIA] Fetching Hebrew/Jewish texts...")
        
        for category, texts in self.TEXTS_TO_FETCH.items():
            logger.info(f"  Category: {category}")
            
            for text_name in texts:
                logger.info(f"    Fetching: {text_name}")
                
                try:
                    text_passages = self._fetch_text(text_name, category)
                    passages.extend(text_passages)
                    logger.info(f"      Got {len(text_passages)} passages")
                except Exception as e:
                    logger.error(f"      Error: {e}")
                
                if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                    break
            
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
        
        self._save_passages(passages)
        logger.info(f"  [OK] Sefaria: {len(passages)} passages")
        return passages
    
    def _fetch_text(self, text_name: str, category: str) -> List[Passage]:
        """Fetch a single text by name"""
        passages = []
        
        # Get text shape to find structure
        shape_url = f"{self.BASE_URL}/shape/{text_name}"
        shape_data = self.client.get(shape_url)
        
        if not shape_data:
            # Try fetching chapters directly
            return self._fetch_chapters_direct(text_name, category, max_chapters=10)
        
        # shape_data is a LIST of section info
        if isinstance(shape_data, list):
            # Each item has 'chapter' and 'length' or similar
            num_sections = len(shape_data)
        elif isinstance(shape_data, dict):
            # Some texts return dict with 'section' key
            num_sections = shape_data.get('length', 10)
        else:
            num_sections = 10
        
        # Fetch each section
        for section in range(1, min(num_sections + 1, 20)):
            passage = self._fetch_section(text_name, section, category)
            if passage:
                passages.append(passage)
            
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
        
        return passages
    
    def _fetch_chapters_direct(self, text_name: str, category: str, max_chapters: int = 10) -> List[Passage]:
        """Fallback: fetch chapters directly without shape"""
        passages = []
        
        for chapter in range(1, max_chapters + 1):
            passage = self._fetch_section(text_name, chapter, category)
            if passage:
                passages.append(passage)
            else:
                # Stop if chapter doesn't exist
                break
        
        return passages
    
    def _fetch_section(self, text_name: str, section: int, category: str) -> Optional[Passage]:
        """Fetch a single section/chapter"""
        
        # Use v3 API for better structure
        url = f"{self.BASE_URL}/v3/texts/{text_name}.{section}"
        data = self.client.get(url)
        
        if not data:
            return None
        
        # Handle v3 response structure
        versions = data.get('versions', [])
        
        # Find Hebrew and English versions
        hebrew_text = ""
        english_text = ""
        
        for version in versions:
            lang = version.get('language', '')
            text = version.get('text', '')
            
            # Flatten nested text arrays
            if isinstance(text, list):
                text = self._flatten_text(text)
            
            if lang == 'he' and not hebrew_text:
                hebrew_text = text
            elif lang == 'en' and not english_text:
                english_text = text
        
        if not hebrew_text and not english_text:
            return None
        
        # Create passage
        ref = data.get('ref', f"{text_name} {section}")
        
        return Passage(
            id=f"sefaria:{text_name}.{section}",
            source="sefaria",
            ref=ref,
            title=text_name.replace('_', ' '),
            text_original=hebrew_text,
            text_english=english_text,
            language="he",
            category=category,
            subcategory=self._get_subcategory(text_name),
            date_composed=self._estimate_date(text_name),
            metadata={
                "sefaria_url": f"https://www.sefaria.org/{text_name}.{section}",
                "section": section,
            }
        )
    
    def _flatten_text(self, text: Any) -> str:
        """Flatten nested text arrays to string"""
        if isinstance(text, str):
            return text
        elif isinstance(text, list):
            parts = []
            for item in text:
                parts.append(self._flatten_text(item))
            return " ".join(parts)
        else:
            return str(text) if text else ""
    
    def _get_subcategory(self, text_name: str) -> str:
        """Get subcategory for text"""
        if "Avot" in text_name:
            return "pirkei_avot"
        elif "Bava" in text_name:
            return "nezikin"
        elif "Derech" in text_name:
            return "derech_eretz"
        elif "Nedarim" in text_name or "Shevuot" in text_name:
            return "oaths_vows"
        else:
            return "mishnah"
    
    def _estimate_date(self, text_name: str) -> str:
        """Estimate composition date"""
        if "Mishnah" in text_name:
            return "200 CE"
        elif "Avot" in text_name:
            return "200 BCE - 200 CE"
        else:
            return "200-500 CE"
    
    def _save_passages(self, passages: List[Passage]):
        """Save passages to JSON"""
        output_file = self.output_dir / "passages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([asdict(p) for p in passages], f, indent=2, ensure_ascii=False)


# =============================================================================
# QURAN FETCHER
# =============================================================================

class QuranFetcher:
    """
    Fetches from AlQuran Cloud API
    """
    
    BASE_URL = "https://api.alquran.cloud/v1"
    
    # SQND-relevant surahs (ethics/law focused)
    SQND_SURAHS = [
        1,   # Al-Fatiha (Opening)
        2,   # Al-Baqarah (The Cow) - legal content
        4,   # An-Nisa (Women) - family law
        5,   # Al-Ma'idah (Table) - contracts, oaths
        17,  # Al-Isra (Night Journey) - ethical commands
        24,  # An-Nur (Light) - social ethics
        49,  # Al-Hujurat (Chambers) - social conduct
        103, # Al-Asr (Time) - human condition
        107, # Al-Ma'un (Small Kindnesses)
    ]
    
    def __init__(self, client: RobustHTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "quran"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        """Fetch SQND-relevant Quran surahs"""
        passages = []
        
        logger.info("[QURAN] Fetching from AlQuran Cloud...")
        
        for surah_num in self.SQND_SURAHS:
            logger.info(f"  Surah {surah_num}")
            
            # Get Arabic + English translation
            url = f"{self.BASE_URL}/surah/{surah_num}/editions/quran-uthmani,en.asad"
            data = self.client.get(url)
            
            if not data or data.get('code') != 200:
                logger.warning(f"    Failed to fetch surah {surah_num}")
                continue
            
            editions = data.get('data', [])
            if len(editions) < 2:
                continue
            
            arabic_data = editions[0]
            english_data = editions[1]
            
            surah_name = arabic_data.get('englishName', f'Surah {surah_num}')
            
            arabic_ayahs = arabic_data.get('ayahs', [])
            english_ayahs = english_data.get('ayahs', [])
            
            # Combine verses into passage (group by ~10 verses for manageable chunks)
            chunk_size = 10
            for i in range(0, len(arabic_ayahs), chunk_size):
                ar_chunk = arabic_ayahs[i:i+chunk_size]
                en_chunk = english_ayahs[i:i+chunk_size]
                
                ar_text = " ".join([a.get('text', '') for a in ar_chunk])
                en_text = " ".join([a.get('text', '') for a in en_chunk])
                
                start_ayah = ar_chunk[0].get('numberInSurah', i+1)
                end_ayah = ar_chunk[-1].get('numberInSurah', i+chunk_size)
                
                passage = Passage(
                    id=f"quran:{surah_num}:{start_ayah}-{end_ayah}",
                    source="quran",
                    ref=f"Quran {surah_num}:{start_ayah}-{end_ayah}",
                    title=surah_name,
                    text_original=ar_text,
                    text_english=en_text,
                    language="ar",
                    category="scripture",
                    subcategory=self._categorize_surah(surah_num),
                    date_composed="610-632 CE",
                    metadata={
                        "surah_number": surah_num,
                        "revelation_type": arabic_data.get('revelationType', ''),
                    }
                )
                passages.append(passage)
            
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
        
        self._save_passages(passages)
        logger.info(f"  [OK] Quran: {len(passages)} passages")
        return passages
    
    def _categorize_surah(self, surah_num: int) -> str:
        """Categorize surah by content"""
        legal_surahs = [2, 4, 5, 24]
        ethical_surahs = [17, 49, 103, 107]
        
        if surah_num in legal_surahs:
            return "legal"
        elif surah_num in ethical_surahs:
            return "ethics"
        else:
            return "general"
    
    def _save_passages(self, passages: List[Passage]):
        output_file = self.output_dir / "passages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([asdict(p) for p in passages], f, indent=2, ensure_ascii=False)


# =============================================================================
# HADITH FETCHER
# =============================================================================

class HadithFetcher:
    """
    Fetches from fawazahmed0's Hadith API
    """
    
    BASE_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"
    
    # Collections to fetch (most authoritative)
    COLLECTIONS = [
        ("eng-bukhari", "Sahih al-Bukhari"),
        ("eng-muslim", "Sahih Muslim"),
        ("eng-abudawud", "Sunan Abu Dawud"),
    ]
    
    # Hadith numbers to fetch (ethics-focused)
    HADITH_RANGES = list(range(1, 101))  # First 100 from each
    
    def __init__(self, client: RobustHTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "hadith"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        """Fetch hadith from major collections"""
        passages = []
        
        logger.info("[HADITH] Fetching from Hadith API...")
        
        for collection_id, collection_name in self.COLLECTIONS:
            logger.info(f"  Collection: {collection_name}")
            
            count = 0
            for hadith_num in self.HADITH_RANGES:
                url = f"{self.BASE_URL}/editions/{collection_id}/{hadith_num}.json"
                data = self.client.get(url)
                
                if not data:
                    continue
                
                hadiths = data.get('hadiths', [])
                if not hadiths:
                    continue
                
                hadith = hadiths[0]
                text = hadith.get('text', '')
                
                if not text:
                    continue
                
                passage = Passage(
                    id=f"hadith:{collection_id}:{hadith_num}",
                    source="hadith",
                    ref=f"{collection_name} #{hadith_num}",
                    title=collection_name,
                    text_original=text,  # API provides English
                    text_english=text,
                    language="en",  # Translation
                    category="hadith",
                    subcategory=collection_id.replace('eng-', ''),
                    date_composed="800-900 CE (compiled)",
                    metadata={
                        "collection": collection_id,
                        "number": hadith_num,
                        "grades": hadith.get('grades', []),
                    }
                )
                passages.append(passage)
                count += 1
                
                if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                    break
            
            logger.info(f"    Got {count} hadiths")
            
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
        
        self._save_passages(passages)
        logger.info(f"  [OK] Hadith: {len(passages)} passages")
        return passages
    
    def _save_passages(self, passages: List[Passage]):
        output_file = self.output_dir / "passages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([asdict(p) for p in passages], f, indent=2, ensure_ascii=False)


# =============================================================================
# BIBLE FETCHER
# =============================================================================

class BibleFetcher:
    """
    Fetches from Bible API (bible-api.com)
    """
    
    BASE_URL = "https://bible-api.com"
    
    # SQND-relevant passages
    PASSAGES = [
        # Torah/Law
        ("Exodus 20:1-17", "Ten Commandments", "torah"),
        ("Leviticus 19:1-18", "Holiness Code", "torah"),
        ("Deuteronomy 6:4-9", "Shema", "torah"),
        
        # Wisdom
        ("Proverbs 3:1-12", "Trust in the Lord", "wisdom"),
        ("Proverbs 6:16-19", "Seven Abominations", "wisdom"),
        ("Ecclesiastes 12:13-14", "Fear God", "wisdom"),
        
        # Prophets
        ("Micah 6:6-8", "What does the Lord require", "prophets"),
        ("Amos 5:21-24", "Let justice roll", "prophets"),
        ("Isaiah 1:16-17", "Learn to do good", "prophets"),
        
        # Sermon on the Mount
        ("Matthew 5:1-12", "Beatitudes", "gospels"),
        ("Matthew 5:38-48", "Love your enemies", "gospels"),
        ("Matthew 6:1-4", "Giving to the needy", "gospels"),
        ("Matthew 7:1-5", "Do not judge", "gospels"),
        ("Matthew 7:12", "Golden Rule", "gospels"),
        
        # Pauline Ethics
        ("Romans 12:9-21", "Love in action", "epistles"),
        ("Romans 13:8-10", "Love fulfills the law", "epistles"),
        ("1 Corinthians 13:1-13", "Love chapter", "epistles"),
        ("Galatians 5:22-23", "Fruit of the Spirit", "epistles"),
        
        # General Epistles
        ("James 1:22-27", "Doers of the word", "epistles"),
        ("James 2:14-17", "Faith and works", "epistles"),
        ("1 John 4:7-12", "God is love", "epistles"),
    ]
    
    def __init__(self, client: RobustHTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "bible"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        """Fetch Bible passages"""
        passages = []
        
        logger.info("[BIBLE] Fetching from Bible API...")
        
        for ref, title, category in self.PASSAGES:
            logger.info(f"  {ref}")
            
            # URL encode reference
            encoded = urllib.parse.quote(ref)
            url = f"{self.BASE_URL}/{encoded}"
            
            data = self.client.get(url)
            if not data:
                continue
            
            text = data.get('text', '')
            if not text:
                continue
            
            passage = Passage(
                id=f"bible:{ref.replace(' ', '_').replace(':', '_')}",
                source="bible",
                ref=ref,
                title=title,
                text_original=text,
                text_english=text,
                language="en",
                category="scripture",
                subcategory=category,
                date_composed=self._estimate_date(category),
                metadata={
                    "translation": data.get('translation_name', 'World English Bible'),
                    "verses": len(data.get('verses', [])),
                }
            )
            passages.append(passage)
            
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
        
        self._save_passages(passages)
        logger.info(f"  [OK] Bible: {len(passages)} passages")
        return passages
    
    def _estimate_date(self, category: str) -> str:
        dates = {
            "torah": "1400-400 BCE",
            "wisdom": "900-200 BCE",
            "prophets": "800-500 BCE",
            "gospels": "50-100 CE",
            "epistles": "50-100 CE",
        }
        return dates.get(category, "Unknown")
    
    def _save_passages(self, passages: List[Passage]):
        output_file = self.output_dir / "passages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([asdict(p) for p in passages], f, indent=2, ensure_ascii=False)


# =============================================================================
# BHAGAVAD GITA FETCHER
# =============================================================================

class GitaFetcher:
    """
    Fetches from vedicscriptures.github.io API
    """
    
    BASE_URL = "https://vedicscriptures.github.io"
    
    # Ethics-heavy chapters
    CHAPTERS = [2, 3, 4, 5, 6, 12, 16, 17, 18]
    
    def __init__(self, client: RobustHTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "gita"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        """Fetch Bhagavad Gita chapters"""
        passages = []
        
        logger.info("[GITA] Fetching Bhagavad Gita...")
        
        for chapter_num in self.CHAPTERS:
            logger.info(f"  Chapter {chapter_num}")
            
            # Get chapter info
            chapter_url = f"{self.BASE_URL}/chapter/{chapter_num}.json"
            chapter_data = self.client.get(chapter_url)
            
            if not chapter_data:
                continue
            
            chapter_name = chapter_data.get('name', f'Chapter {chapter_num}')
            verses_count = chapter_data.get('verses_count', 20)
            
            # Fetch verses
            for verse_num in range(1, min(verses_count + 1, 50)):
                verse_url = f"{self.BASE_URL}/slok/{chapter_num}/{verse_num}.json"
                verse_data = self.client.get(verse_url)
                
                if not verse_data:
                    continue
                
                sanskrit = verse_data.get('slok', '')
                
                # Get English translation (try multiple translators)
                english = ""
                for translator in ['tej', 'spitr', 'rpitr', 'adi', 'gambir']:
                    trans = verse_data.get(translator, {})
                    if isinstance(trans, dict):
                        english = trans.get('et', '')
                        if english:
                            break
                
                if not sanskrit and not english:
                    continue
                
                passage = Passage(
                    id=f"gita:{chapter_num}:{verse_num}",
                    source="bhagavad_gita",
                    ref=f"Bhagavad Gita {chapter_num}.{verse_num}",
                    title=chapter_name,
                    text_original=sanskrit,
                    text_english=english,
                    language="sa",
                    category="scripture",
                    subcategory="gita",
                    date_composed="200 BCE - 200 CE",
                    metadata={
                        "chapter": chapter_num,
                        "verse": verse_num,
                        "transliteration": verse_data.get('transliteration', ''),
                    }
                )
                passages.append(passage)
            
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
        
        self._save_passages(passages)
        logger.info(f"  [OK] Gita: {len(passages)} passages")
        return passages
    
    def _save_passages(self, passages: List[Passage]):
        output_file = self.output_dir / "passages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([asdict(p) for p in passages], f, indent=2, ensure_ascii=False)


# =============================================================================
# SUTTACENTRAL FETCHER (Buddhist)
# =============================================================================

class SuttaCentralFetcher:
    """
    Fetches from SuttaCentral API
    """
    
    BASE_URL = "https://suttacentral.net/api"
    
    # Key ethical suttas
    SUTTAS = [
        "dn31",   # Sigalovada Sutta (householder ethics)
        "mn41",   # Saleyyaka Sutta (wholesome/unwholesome)
        "mn61",   # Ambalatthika-rahulovada (instruction to Rahula)
        "an8.39", # Abhisanda Sutta (streams of merit)
        "an10.176", # Cunda Kammaraputta Sutta (bodily/verbal/mental conduct)
        "sn55.7", # Veludvareyya (Golden Rule passage)
    ]
    
    def __init__(self, client: RobustHTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "buddhist"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        """Fetch Buddhist suttas"""
        passages = []
        
        logger.info("[BUDDHIST] Fetching from SuttaCentral...")
        
        for sutta_id in self.SUTTAS:
            logger.info(f"  Sutta {sutta_id}")
            
            # Get sutta info
            info_url = f"{self.BASE_URL}/suttaplex/{sutta_id}"
            info_data = self.client.get(info_url)
            
            if not info_data:
                continue
            
            # info_data is a list
            if isinstance(info_data, list) and len(info_data) > 0:
                info = info_data[0]
            else:
                info = info_data
            
            title = info.get('original_title', sutta_id)
            translated_title = info.get('translated_title', '')
            
            # Get text
            text_url = f"{self.BASE_URL}/bilarasuttas/{sutta_id}/sujato"
            text_data = self.client.get(text_url)
            
            pali_text = ""
            english_text = ""
            
            if text_data:
                # Extract text from bilara format
                root_text = text_data.get('root_text', {})
                translation = text_data.get('translation_text', {})
                
                # Combine segments
                pali_parts = []
                english_parts = []
                
                for key in sorted(root_text.keys()):
                    pali_parts.append(root_text.get(key, ''))
                    english_parts.append(translation.get(key, ''))
                
                pali_text = " ".join(p for p in pali_parts if p)[:2000]
                english_text = " ".join(e for e in english_parts if e)[:2000]
            
            if not pali_text and not english_text:
                continue
            
            passage = Passage(
                id=f"sutta:{sutta_id}",
                source="suttacentral",
                ref=f"SuttaCentral {sutta_id}",
                title=f"{title} ({translated_title})" if translated_title else title,
                text_original=pali_text,
                text_english=english_text,
                language="pi",
                category="scripture",
                subcategory="sutta",
                date_composed="500-200 BCE",
                metadata={
                    "sutta_id": sutta_id,
                    "nikaya": info.get('acronym', ''),
                }
            )
            passages.append(passage)
            
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
        
        # Add embedded samples for Dhammapada etc.
        passages.extend(self._get_embedded_samples())
        
        self._save_passages(passages)
        logger.info(f"  [OK] Buddhist: {len(passages)} passages")
        return passages
    
    def _get_embedded_samples(self) -> List[Passage]:
        """Embedded key passages"""
        samples = [
            {
                "id": "dhp:1-2",
                "ref": "Dhammapada 1-2",
                "title": "Dhammapada",
                "pali": "Manopubbangama dhamma manosettha manomaya. Manasa ce padutthena bhasati va karoti va, tato nam dukkhamanveti cakkam va vahato padam.",
                "english": "Mind is the forerunner of all actions. All deeds are led by mind, created by mind. If one speaks or acts with a corrupt mind, suffering follows, as the wheel follows the hoof of an ox pulling a cart.",
            },
            {
                "id": "dhp:129-130",
                "ref": "Dhammapada 129-130",
                "title": "Dhammapada - Golden Rule",
                "pali": "Sabbe tasanti dandassa sabbe bhayanti maccuno. Attanam upamam katva na haneyya na ghataye.",
                "english": "All tremble at punishment, all fear death. Comparing others with oneself, one should neither kill nor cause to kill.",
            },
        ]
        
        passages = []
        for s in samples:
            passages.append(Passage(
                id=f"sutta:{s['id']}",
                source="dhammapada",
                ref=s["ref"],
                title=s["title"],
                text_original=s["pali"],
                text_english=s["english"],
                language="pi",
                category="scripture",
                subcategory="dhammapada",
                date_composed="300 BCE",
                metadata={"embedded": True},
            ))
        
        return passages
    
    def _save_passages(self, passages: List[Passage]):
        output_file = self.output_dir / "passages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([asdict(p) for p in passages], f, indent=2, ensure_ascii=False)


# =============================================================================
# COURTLISTENER FETCHER
# =============================================================================

class CourtListenerFetcher:
    """
    Fetches from CourtListener API (US Case Law)
    
    Note: Works without API key for basic search, but limited.
    """
    
    BASE_URL = "https://www.courtlistener.com/api/rest/v4"
    
    # Search queries for SQND-relevant cases
    SEARCHES = [
        ("contract breach", "contract_law"),
        ("tort negligence", "tort_law"),
        ("due process", "constitutional"),
        ("equal protection", "civil_rights"),
        ("fiduciary duty", "fiduciary"),
    ]
    
    def __init__(self, client: RobustHTTPClient, config: FetcherConfig):
        self.client = client
        self.config = config
        self.output_dir = Path(config.output_dir) / "courtlistener"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = config.courtlistener_api_key
    
    def fetch_all(self) -> List[Passage]:
        """Fetch US case law"""
        passages = []
        
        logger.info("[COURTLISTENER] Fetching US Case Law...")
        
        if self.api_key:
            headers = {"Authorization": f"Token {self.api_key}"}
        else:
            headers = {}
            logger.warning("  No API key - limited results")
        
        for query, category in self.SEARCHES:
            logger.info(f"  Query: {query}")
            
            search_url = f"{self.BASE_URL}/search/"
            params = f"?q={urllib.parse.quote(query)}&type=o"
            
            # Note: CourtListener may require auth for full results
            data = self.client.get(search_url + params, headers=headers)
            
            if not data:
                continue
            
            results = data.get('results', [])
            
            for result in results[:10]:  # First 10 per query
                case_name = result.get('caseName', 'Unknown Case')
                snippet = result.get('snippet', '')
                court = result.get('court', '')
                date_filed = result.get('dateFiled', '')
                
                if not snippet:
                    continue
                
                # Clean HTML from snippet
                snippet = snippet.replace('<mark>', '').replace('</mark>', '')
                
                passage = Passage(
                    id=f"cl:{result.get('id', '')}",
                    source="courtlistener",
                    ref=case_name,
                    title=case_name,
                    text_original=snippet,
                    text_english=snippet,
                    language="en",
                    category="legal",
                    subcategory=category,
                    date_composed=date_filed or "Unknown",
                    metadata={
                        "court": court,
                        "url": result.get('absolute_url', ''),
                    }
                )
                passages.append(passage)
            
            if self.config.limit_per_source and len(passages) >= self.config.limit_per_source:
                break
        
        self._save_passages(passages)
        logger.info(f"  [OK] CourtListener: {len(passages)} passages")
        return passages
    
    def _save_passages(self, passages: List[Passage]):
        output_file = self.output_dir / "passages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([asdict(p) for p in passages], f, indent=2, ensure_ascii=False)


# =============================================================================
# EMBEDDED SAMPLES (for APIs that don't work)
# =============================================================================

class EmbeddedSamplesFetcher:
    """
    Provides embedded samples for sources without working APIs:
    - Chinese classics (CText returns 403)
    - Greek/Roman philosophy (Perseus has no REST API)
    - Roman Law (Digest - no API)
    - Upanishads
    """
    
    def __init__(self, client: RobustHTTPClient, config: FetcherConfig):
        self.config = config
        self.output_dir = Path(config.output_dir) / "embedded"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all(self) -> List[Passage]:
        """Return all embedded samples"""
        passages = []
        
        logger.info("[EMBEDDED] Loading embedded samples...")
        
        passages.extend(self._chinese_samples())
        passages.extend(self._greek_roman_samples())
        passages.extend(self._roman_law_samples())
        passages.extend(self._upanishad_samples())
        
        self._save_passages(passages)
        logger.info(f"  [OK] Embedded: {len(passages)} passages")
        return passages
    
    def _chinese_samples(self) -> List[Passage]:
        """Confucian and Taoist texts"""
        samples = [
            {
                "ref": "Analects 4:15",
                "title": "Analects of Confucius",
                "chinese": "子曰：「參乎！吾道一以貫之。」曾子曰：「唯。」子出，門人問曰：「何謂也？」曾子曰：「夫子之道，忠恕而已矣。」",
                "english": "The Master said, 'Shen, my doctrine is all pervaded by one principle.' Zengzi replied, 'Yes.' When the Master went out, the disciples asked, 'What did he mean?' Zengzi said, 'The doctrine of our master is to be true to the principles of our nature (zhong) and the benevolent exercise of them to others (shu), that is all.'",
                "category": "reciprocity",
            },
            {
                "ref": "Analects 12:2",
                "title": "Analects of Confucius",
                "chinese": "仲弓問仁。子曰：「出門如見大賓，使民如承大祭。己所不欲，勿施於人。在邦無怨，在家無怨。」",
                "english": "Zhonggong asked about ren (humaneness). The Master said, 'Go out of your home as if you were receiving a great guest. Employ the people as if you were assisting at a great sacrifice. Do not do to others what you would not wish done to yourself. Then there will be no resentment against you, either in the state or in the family.'",
                "category": "golden_rule",
            },
            {
                "ref": "Analects 15:24",
                "title": "Analects of Confucius - Golden Rule",
                "chinese": "子貢問曰：「有一言而可以終身行之者乎？」子曰：「其恕乎！己所不欲，勿施於人。」",
                "english": "Zigong asked, 'Is there one word that can serve as a principle for the conduct of life?' The Master replied, 'Perhaps the word shu (reciprocity): Do not do to others what you would not want done to yourself.'",
                "category": "golden_rule",
            },
            {
                "ref": "Mencius 7A:4",
                "title": "Mencius",
                "chinese": "萬物皆備於我矣。反身而誠，樂莫大焉。強恕而行，求仁莫近焉。",
                "english": "All things are complete in us. There is no greater delight than to find sincerity when one examines oneself. If one acts with a strong commitment to shu (reciprocity), there is no closer path to ren (humaneness).",
                "category": "ethics",
            },
            {
                "ref": "Tao Te Ching 63",
                "title": "Tao Te Ching",
                "chinese": "為無為，事無事，味無味。大小多少，報怨以德。",
                "english": "Act without acting; serve without serving; taste without tasting. Regard the small as great, the few as many. Respond to injury with virtue.",
                "category": "non_retaliation",
            },
        ]
        
        passages = []
        for s in samples:
            passages.append(Passage(
                id=f"chinese:{s['ref'].replace(' ', '_')}",
                source="chinese_classics",
                ref=s["ref"],
                title=s["title"],
                text_original=s["chinese"],
                text_english=s["english"],
                language="zh",
                category="philosophy",
                subcategory=s["category"],
                date_composed="500-200 BCE",
                metadata={"embedded": True},
            ))
        
        return passages
    
    def _greek_roman_samples(self) -> List[Passage]:
        """Greek and Roman philosophy"""
        samples = [
            {
                "ref": "Nicomachean Ethics 1094a",
                "author": "Aristotle",
                "english": "Every art and every inquiry, and similarly every action and pursuit, is thought to aim at some good; and for this reason the good has rightly been declared to be that at which all things aim.",
                "category": "teleology",
                "date": "350 BCE",
            },
            {
                "ref": "Nicomachean Ethics 1106b",
                "author": "Aristotle",
                "english": "Virtue, then, is a state of character concerned with choice, lying in a mean, i.e. the mean relative to us, this being determined by reason, and by that reason by which the man of practical wisdom would determine it.",
                "category": "virtue_ethics",
                "date": "350 BCE",
            },
            {
                "ref": "Republic 331c",
                "author": "Plato",
                "english": "Speaking the truth and paying back what one has received is not the definition of justice.",
                "category": "justice",
                "date": "380 BCE",
            },
            {
                "ref": "Crito 49b-c",
                "author": "Plato",
                "english": "We ought not to retaliate or render evil for evil to anyone, whatever evil we may have suffered from him.",
                "category": "non_retaliation",
                "date": "380 BCE",
            },
            {
                "ref": "Meditations 2.1",
                "author": "Marcus Aurelius",
                "english": "Begin the morning by saying to yourself: I shall meet with the busybody, the ungrateful, arrogant, deceitful, envious, unsocial. All these things happen to them by reason of their ignorance of what is good and evil.",
                "category": "stoic_ethics",
                "date": "170 CE",
            },
            {
                "ref": "Enchiridion 1",
                "author": "Epictetus",
                "english": "Some things are in our control and others not. Things in our control are opinion, pursuit, desire, aversion, and, in a word, whatever are our own actions. Things not in our control are body, property, reputation, command.",
                "category": "stoic_ethics",
                "date": "135 CE",
            },
            {
                "ref": "Letters 95.52",
                "author": "Seneca",
                "english": "Let us show our generosity in the same manner that we would wish to have it bestowed on us.",
                "category": "reciprocity",
                "date": "65 CE",
            },
        ]
        
        passages = []
        for s in samples:
            passages.append(Passage(
                id=f"perseus:{s['author'].lower()}:{s['ref'].replace(' ', '_')}",
                source="greek_roman",
                ref=f"{s['author']}, {s['ref']}",
                title=s['ref'].split()[0],
                text_original=s["english"],  # No Greek available in samples
                text_english=s["english"],
                language="grc",
                category="philosophy",
                subcategory=s["category"],
                date_composed=s["date"],
                metadata={"author": s["author"], "embedded": True},
            ))
        
        return passages
    
    def _roman_law_samples(self) -> List[Passage]:
        """Justinian's Digest"""
        samples = [
            {
                "ref": "D.1.1.1pr",
                "jurist": "Ulpian",
                "latin": "Iuri operam daturum prius nosse oportet, unde nomen iuris descendat. est autem a iustitia appellatum: nam, ut eleganter Celsus definit, ius est ars boni et aequi.",
                "english": "One who is going to study law ought first to know whence the word 'law' derives. It is called from 'justice'; for, as Celsus elegantly defines it, law is the art of the good and the fair.",
                "topic": "definition_of_law",
            },
            {
                "ref": "D.1.1.10pr",
                "jurist": "Ulpian",
                "latin": "Iustitia est constans et perpetua voluntas ius suum cuique tribuendi.",
                "english": "Justice is the constant and perpetual will to render to each one his right.",
                "topic": "definition_of_justice",
            },
            {
                "ref": "D.1.1.10.1",
                "jurist": "Ulpian",
                "latin": "Iuris praecepta sunt haec: honeste vivere, alterum non laedere, suum cuique tribuere.",
                "english": "The precepts of the law are these: to live honestly, to harm no one, to give to each his own.",
                "topic": "three_precepts",
            },
            {
                "ref": "D.50.17.54",
                "jurist": "Gaius",
                "latin": "Nullus videtur dolo facere, qui suo iure utitur.",
                "english": "No one is considered to act with malice who exercises his own right.",
                "topic": "rights",
            },
            {
                "ref": "D.4.2.1",
                "jurist": "Ulpian",
                "latin": "Ait praetor: 'Quod metus causa gestum erit, ratum non habebo.'",
                "english": "The praetor says: 'What has been done through fear, I will not uphold.'",
                "topic": "duress",
            },
            {
                "ref": "D.50.17.185",
                "jurist": "Celsus",
                "latin": "Impossibilium nulla obligatio est.",
                "english": "There is no obligation to do the impossible.",
                "topic": "impossibility",
            },
            {
                "ref": "D.12.6.14",
                "jurist": "Pomponius",
                "latin": "Nam hoc natura aequum est neminem cum alterius detrimento fieri locupletiorem.",
                "english": "For by nature it is equitable that no one should be enriched at another's expense.",
                "topic": "unjust_enrichment",
            },
        ]
        
        passages = []
        for s in samples:
            passages.append(Passage(
                id=f"digest:{s['ref']}",
                source="roman_law",
                ref=f"Digest {s['ref']}",
                title=f"Digest - {s['jurist']}",
                text_original=s["latin"],
                text_english=s["english"],
                language="la",
                category="legal",
                subcategory=s["topic"],
                date_composed="533 CE",
                metadata={"jurist": s["jurist"], "embedded": True},
            ))
        
        return passages
    
    def _upanishad_samples(self) -> List[Passage]:
        """Hindu Upanishads"""
        samples = [
            {
                "ref": "Isha Upanishad 1",
                "sanskrit": "ईशावास्यमिदं सर्वं यत्किञ्च जगत्यां जगत्",
                "english": "All this, whatever moves in this moving world, is pervaded by the Lord. Therefore find your enjoyment in renunciation; do not covet what belongs to others.",
            },
            {
                "ref": "Brihadaranyaka 1.4.14",
                "sanskrit": "आत्मानं चेद्विजानीयात्",
                "english": "If one knows the Self, with 'I am Brahman', becoming everything, even the gods cannot prevent him, for he becomes their Self.",
            },
            {
                "ref": "Chandogya 6.8.7",
                "sanskrit": "तत्त्वमसि",
                "english": "That thou art. You are that ultimate reality, that Brahman.",
            },
            {
                "ref": "Mundaka 3.1.6",
                "sanskrit": "सत्यमेव जयते",
                "english": "Truth alone triumphs, not falsehood. By truth is laid out the path leading to the gods.",
            },
        ]
        
        passages = []
        for s in samples:
            passages.append(Passage(
                id=f"upanishad:{s['ref'].replace(' ', '_')}",
                source="upanishads",
                ref=s["ref"],
                title=s["ref"].split()[0] + " Upanishad",
                text_original=s["sanskrit"],
                text_english=s["english"],
                language="sa",
                category="scripture",
                subcategory="upanishad",
                date_composed="800-200 BCE",
                metadata={"embedded": True},
            ))
        
        return passages
    
    def _save_passages(self, passages: List[Passage]):
        output_file = self.output_dir / "passages.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([asdict(p) for p in passages], f, indent=2, ensure_ascii=False)


# =============================================================================
# CORPUS COMBINER
# =============================================================================

class CorpusCombiner:
    """Combines all fetched passages into unified corpus"""
    
    def __init__(self, config: FetcherConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
    
    def combine_all(self) -> Dict[str, Any]:
        """Combine all source passages"""
        all_passages = []
        stats = {"sources": {}}
        
        # Find all passages.json files
        for source_dir in self.output_dir.iterdir():
            if source_dir.is_dir() and source_dir.name != ".cache":
                passages_file = source_dir / "passages.json"
                if passages_file.exists():
                    with open(passages_file, "r", encoding="utf-8") as f:
                        passages = json.load(f)
                        all_passages.extend(passages)
                        stats["sources"][source_dir.name] = len(passages)
        
        stats["total_passages"] = len(all_passages)
        stats["generated_at"] = datetime.now().isoformat()
        
        # Save combined corpus
        combined_file = self.output_dir / "combined_corpus.json"
        with open(combined_file, "w", encoding="utf-8") as f:
            json.dump(all_passages, f, indent=2, ensure_ascii=False)
        
        # Save stats
        stats_file = self.output_dir / "corpus_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        
        logger.info("\n=== CORPUS STATISTICS ===")
        logger.info(f"Total passages: {stats['total_passages']}")
        for source, count in stats["sources"].items():
            logger.info(f"  {source}: {count}")
        
        return stats


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Ethics Corpus Fetcher v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Source selection
    parser.add_argument("--all", action="store_true", help="Fetch from all sources")
    parser.add_argument("--sefaria", action="store_true", help="Fetch Hebrew/Jewish texts")
    parser.add_argument("--quran", action="store_true", help="Fetch Quran")
    parser.add_argument("--hadith", action="store_true", help="Fetch Hadith")
    parser.add_argument("--bible", action="store_true", help="Fetch Bible")
    parser.add_argument("--gita", action="store_true", help="Fetch Bhagavad Gita")
    parser.add_argument("--buddhist", action="store_true", help="Fetch Buddhist texts")
    parser.add_argument("--courtlistener", action="store_true", help="Fetch US Case Law")
    parser.add_argument("--embedded", action="store_true", help="Include embedded samples")
    
    # Options
    parser.add_argument("--limit", type=int, help="Limit passages per source")
    parser.add_argument("--output", default="./corpus", help="Output directory")
    parser.add_argument("--rate-limit", type=float, default=1.0, help="Seconds between requests")
    
    args = parser.parse_args()
    
    # If no sources specified, show help
    if not any([args.all, args.sefaria, args.quran, args.hadith, args.bible,
                args.gita, args.buddhist, args.courtlistener, args.embedded]):
        parser.print_help()
        return
    
    # Configure
    config = FetcherConfig(
        output_dir=args.output,
        rate_limit_delay=args.rate_limit,
        limit_per_source=args.limit,
        courtlistener_api_key=os.environ.get("COURTLISTENER_API_KEY"),
    )
    
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    client = RobustHTTPClient(config)
    
    print("=" * 60)
    print("COMPREHENSIVE ETHICS CORPUS FETCHER v2")
    print("=" * 60)
    print(f"Output: {config.output_dir}")
    print(f"Rate limit: {config.rate_limit_delay}s")
    if config.limit_per_source:
        print(f"Limit: {config.limit_per_source} per source")
    print("=" * 60)
    
    # Fetch
    all_passages = []
    
    if args.all or args.sefaria:
        fetcher = SefariaFetcher(client, config)
        all_passages.extend(fetcher.fetch_all())
    
    if args.all or args.quran:
        fetcher = QuranFetcher(client, config)
        all_passages.extend(fetcher.fetch_all())
    
    if args.all or args.hadith:
        fetcher = HadithFetcher(client, config)
        all_passages.extend(fetcher.fetch_all())
    
    if args.all or args.bible:
        fetcher = BibleFetcher(client, config)
        all_passages.extend(fetcher.fetch_all())
    
    if args.all or args.gita:
        fetcher = GitaFetcher(client, config)
        all_passages.extend(fetcher.fetch_all())
    
    if args.all or args.buddhist:
        fetcher = SuttaCentralFetcher(client, config)
        all_passages.extend(fetcher.fetch_all())
    
    if args.all or args.courtlistener:
        fetcher = CourtListenerFetcher(client, config)
        all_passages.extend(fetcher.fetch_all())
    
    if args.all or args.embedded:
        fetcher = EmbeddedSamplesFetcher(client, config)
        all_passages.extend(fetcher.fetch_all())
    
    # Combine
    combiner = CorpusCombiner(config)
    stats = combiner.combine_all()
    
    print("\n" + "=" * 60)
    print("[DONE] FETCH COMPLETE")
    print("=" * 60)
    print(f"Total passages: {stats['total_passages']}")
    print(f"Output: {config.output_dir}/combined_corpus.json")


if __name__ == "__main__":
    main()
