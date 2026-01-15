"""
Sefaria API Client v2 - Production-Ready
=========================================

Proper integration with Sefaria's API based on official documentation:
- https://developers.sefaria.org/reference/get-v3-texts
- https://developers.sefaria.org/reference/get-index
- https://developers.sefaria.org/reference/get-shape
- https://developers.sefaria.org/reference/get-related

Key Endpoints:
- /api/index - Full table of contents
- /api/v3/texts/{ref} - Text content with versions
- /api/related/{ref} - Linked commentaries
- /api/shape/{title} - Text structure metadata
- /api/calendars - Daily/weekly readings

Rate Limit: Be respectful (~1 req/sec recommended)
"""

import requests
import json
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class SefariaConfig:
    """Configuration for Sefaria API client"""
    base_url: str = "https://www.sefaria.org"
    cache_dir: str = "./sefaria_cache"
    rate_limit_delay: float = 1.0  # seconds between requests
    cache_expiry_days: int = 7
    timeout: int = 30
    max_retries: int = 3
    

# =============================================================================
# API CLIENT
# =============================================================================

class SefariaAPIClient:
    """
    Production-ready Sefaria API client.
    
    Features:
    - Proper endpoint usage per documentation
    - Caching with expiry
    - Rate limiting
    - Retry logic
    - Comprehensive error handling
    """
    
    def __init__(self, config: SefariaConfig = None):
        self.config = config or SefariaConfig()
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.last_request_time = 0
        self.request_count = 0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SQND-Research/2.0 (Ethics Module Generator)"
        })
        
    def _rate_limit(self):
        """Respect rate limits"""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.config.rate_limit_delay:
            time.sleep(self.config.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
        
    def _cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _cache_path(self, key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{key}.json"
    
    def _read_cache(self, url: str) -> Optional[Dict]:
        """Read from cache if valid"""
        key = self._cache_key(url)
        path = self._cache_path(key)
        
        if not path.exists():
            return None
            
        try:
            with open(path) as f:
                cached = json.load(f)
                
            # Check expiry
            cached_time = datetime.fromisoformat(cached.get("_cached_at", "2000-01-01"))
            age_days = (datetime.now() - cached_time).days
            
            if age_days > self.config.cache_expiry_days:
                return None
                
            return cached.get("data")
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None
    
    def _write_cache(self, url: str, data: Dict):
        """Write to cache"""
        key = self._cache_key(url)
        path = self._cache_path(key)
        
        try:
            with open(path, "w") as f:
                json.dump({
                    "_cached_at": datetime.now().isoformat(),
                    "_url": url,
                    "data": data
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request with caching and retry"""
        url = f"{self.config.base_url}{endpoint}"
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{param_str}"
        
        # Check cache
        cached = self._read_cache(url)
        if cached is not None:
            logger.debug(f"Cache hit: {endpoint}")
            return cached
        
        # Rate limit
        self._rate_limit()
        
        # Make request with retry
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(url, timeout=self.config.timeout)
                response.raise_for_status()
                data = response.json()
                
                # Cache successful response
                self._write_cache(url, data)
                self.request_count += 1
                
                return data
                
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception(f"Request failed after {self.config.max_retries} attempts: {last_error}")
    
    # =========================================================================
    # INDEX ENDPOINTS
    # =========================================================================
    
    def get_table_of_contents(self) -> List[Dict]:
        """
        GET /api/index
        
        Returns the full table of contents - all texts organized by category.
        This is a large request - cache it!
        """
        return self._get("/api/index")
    
    def get_index_v2(self, title: str) -> Dict:
        """
        GET /api/v2/raw/index/{title}
        
        Get full index record for a specific text.
        """
        return self._get(f"/api/v2/raw/index/{title}")
    
    def get_shape(self, title: str) -> Dict:
        """
        GET /api/shape/{title}
        
        Get structure/shape information for a text.
        Returns chapter counts, section depths, etc.
        """
        return self._get(f"/api/shape/{title}")
    
    # =========================================================================
    # TEXT ENDPOINTS
    # =========================================================================
    
    def get_text_v3(self, ref: str, version: str = None) -> Dict:
        """
        GET /api/v3/texts/{ref}
        
        Get text content with all available versions.
        
        Args:
            ref: Sefaria reference (e.g., "Pirkei_Avot.1.1", "Bava_Metzia.75b")
            version: Optional version filter ("english", "hebrew", or specific version name)
        """
        params = {}
        if version:
            params["version"] = version
        return self._get(f"/api/v3/texts/{ref}", params)
    
    def get_text_v1(self, ref: str) -> Dict:
        """
        GET /api/texts/{ref}
        
        Legacy text endpoint (v1).
        """
        return self._get(f"/api/texts/{ref}")
    
    def get_random_text(self) -> Dict:
        """
        GET /api/texts/random
        
        Get a random text from the library.
        """
        return self._get("/api/texts/random")
    
    # =========================================================================
    # RELATED ENDPOINTS
    # =========================================================================
    
    def get_related(self, ref: str) -> Dict:
        """
        GET /api/related/{ref}
        
        Get all content related to a text:
        - links (commentaries, cross-references)
        - sheets
        - notes
        - webpages
        - topics
        - manuscripts
        - media
        """
        return self._get(f"/api/related/{ref}")
    
    def get_links(self, ref: str) -> List[Dict]:
        """
        GET /api/links/{ref}
        
        Get just the links/connections for a text.
        """
        return self._get(f"/api/links/{ref}")
    
    # =========================================================================
    # CALENDAR ENDPOINTS
    # =========================================================================
    
    def get_calendars(self) -> Dict:
        """
        GET /api/calendars
        
        Get current calendar items:
        - Parashat Hashavua (weekly Torah portion)
        - Haftarah
        - Daf Yomi
        - etc.
        """
        return self._get("/api/calendars")
    
    # =========================================================================
    # SEARCH ENDPOINTS
    # =========================================================================
    
    def search(self, query: str, filters: Dict = None, size: int = 100) -> Dict:
        """
        POST /api/search-wrapper/text/{query}
        
        Search across the library.
        """
        # Note: This is actually a GET despite the docs
        endpoint = f"/api/search-wrapper/text/{query}"
        params = {"size": size}
        if filters:
            params.update(filters)
        return self._get(endpoint, params)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_all_texts_in_category(self, category: str) -> List[str]:
        """Get all text titles in a category"""
        toc = self.get_table_of_contents()
        titles = []
        
        def extract_titles(node, path=""):
            if isinstance(node, dict):
                current_cat = node.get("category", "")
                if current_cat == category or category in path:
                    if "title" in node:
                        titles.append(node["title"])
                for key, value in node.items():
                    extract_titles(value, f"{path}/{current_cat}")
            elif isinstance(node, list):
                for item in node:
                    extract_titles(item, path)
        
        extract_titles(toc)
        return titles
    
    def iter_text_sections(self, title: str, max_sections: int = None) -> List[Tuple[str, Dict]]:
        """
        Iterate through all sections of a text.
        
        Yields (ref, text_data) tuples.
        """
        shape = self.get_shape(title)
        sections = []
        
        # Parse shape to get valid refs
        if "section" in shape:
            # Simple text
            count = shape.get("length", 10)
            for i in range(1, min(count + 1, max_sections or count + 1)):
                ref = f"{title}.{i}"
                try:
                    data = self.get_text_v3(ref)
                    sections.append((ref, data))
                except Exception as e:
                    logger.warning(f"Failed to fetch {ref}: {e}")
                    break
        else:
            # Complex text - just fetch first N chapters
            for i in range(1, (max_sections or 10) + 1):
                ref = f"{title}.{i}"
                try:
                    data = self.get_text_v3(ref)
                    if data.get("versions"):
                        sections.append((ref, data))
                except Exception as e:
                    logger.debug(f"No more sections at {ref}")
                    break
        
        return sections


# =============================================================================
# SQND-RELEVANT TEXTS
# =============================================================================

# Texts organized by SQND relevance
SQND_TEXT_CATALOG = {
    "ethics": {
        "description": "Ethical maxims and moral teachings",
        "texts": [
            "Pirkei_Avot",           # Ethics of the Fathers
            "Derech_Eretz_Rabbah",   # Major tractate on proper conduct
            "Derech_Eretz_Zuta",     # Minor tractate on proper conduct
        ],
        "sqnd_relevance": "High - direct moral principles"
    },
    
    "civil_law": {
        "description": "Torts, property, commerce - Hohfeldian goldmine",
        "texts": [
            "Mishnah_Bava_Kamma",    # Damages, injuries
            "Mishnah_Bava_Metzia",   # Found property, wages, bailment
            "Mishnah_Bava_Batra",    # Property rights, inheritance
            "Bava_Kamma",            # Talmud expansion
            "Bava_Metzia",           # Talmud expansion
            "Bava_Batra",            # Talmud expansion
        ],
        "sqnd_relevance": "Critical - explicit O/C/L/N structures"
    },
    
    "vows_oaths": {
        "description": "Binding commitments - BINDING gates",
        "texts": [
            "Mishnah_Nedarim",       # Vows
            "Mishnah_Shevuot",       # Oaths
            "Nedarim",               # Talmud
            "Shevuot",               # Talmud
        ],
        "sqnd_relevance": "Critical - L→O transition mechanisms"
    },
    
    "family_law": {
        "description": "Marriage, divorce - correlative structures",
        "texts": [
            "Mishnah_Kiddushin",     # Marriage
            "Mishnah_Gittin",        # Divorce
            "Mishnah_Ketubot",       # Marriage contracts
        ],
        "sqnd_relevance": "High - mutual O↔C obligations"
    },
    
    "courts": {
        "description": "Judicial procedure - legitimacy dimension",
        "texts": [
            "Mishnah_Sanhedrin",     # Courts, capital cases
            "Mishnah_Makkot",        # Punishments
            "Sanhedrin",             # Talmud
        ],
        "sqnd_relevance": "Moderate - procedural legitimacy"
    },
}


# =============================================================================
# CORPUS BUILDER
# =============================================================================

@dataclass
class AnnotatedPassage:
    """A passage with SQND annotations"""
    ref: str
    hebrew: str
    english: str
    title: str
    category: str
    
    # SQND annotations (to be filled by analysis)
    primary_state: Optional[str] = None
    correlative_state: Optional[str] = None
    gate_type: Optional[str] = None
    gate_trigger: Optional[str] = None
    dimensions: Dict[str, float] = field(default_factory=dict)
    consensus_level: str = "unknown"
    
    # Metadata
    source_version: str = ""
    related_refs: List[str] = field(default_factory=list)


class SQNDCorpusBuilder:
    """
    Builds an SQND-annotated corpus from Sefaria.
    
    Workflow:
    1. Fetch text structure via /api/shape
    2. Iterate through sections via /api/v3/texts
    3. Get commentaries via /api/related
    4. Apply SQND pattern detection
    5. Export annotated corpus
    """
    
    def __init__(self, client: SefariaAPIClient = None):
        self.client = client or SefariaAPIClient()
        self.corpus: List[AnnotatedPassage] = []
        
    def build_from_catalog(
        self,
        categories: List[str] = None,
        max_per_text: int = 20,
        include_commentaries: bool = True
    ) -> List[AnnotatedPassage]:
        """
        Build corpus from SQND text catalog.
        
        Args:
            categories: Which categories to include (default: all)
            max_per_text: Maximum passages per text
            include_commentaries: Whether to fetch related commentaries
        """
        if categories is None:
            categories = list(SQND_TEXT_CATALOG.keys())
        
        total_texts = sum(
            len(SQND_TEXT_CATALOG[cat]["texts"]) 
            for cat in categories
        )
        
        logger.info(f"Building corpus from {len(categories)} categories, {total_texts} texts")
        
        for category in categories:
            cat_data = SQND_TEXT_CATALOG.get(category, {})
            texts = cat_data.get("texts", [])
            
            logger.info(f"\n📚 Category: {category}")
            logger.info(f"   {cat_data.get('description', '')}")
            
            for text_title in texts:
                logger.info(f"   📖 Fetching: {text_title}")
                
                try:
                    passages = self._fetch_text_passages(
                        text_title, 
                        category,
                        max_sections=max_per_text
                    )
                    
                    if include_commentaries:
                        for passage in passages[:5]:  # Limit commentary fetches
                            self._enrich_with_commentaries(passage)
                    
                    self.corpus.extend(passages)
                    logger.info(f"      Added {len(passages)} passages")
                    
                except Exception as e:
                    logger.error(f"      Error: {e}")
        
        logger.info(f"\n✅ Corpus built: {len(self.corpus)} passages")
        return self.corpus
    
    def _fetch_text_passages(
        self, 
        title: str, 
        category: str,
        max_sections: int = 20
    ) -> List[AnnotatedPassage]:
        """Fetch passages from a text"""
        passages = []
        
        for ref, data in self.client.iter_text_sections(title, max_sections):
            versions = data.get("versions", [])
            
            hebrew = ""
            english = ""
            he_version = ""
            en_version = ""
            
            for v in versions:
                text = v.get("text", "")
                if isinstance(text, list):
                    text = " ".join(str(t) for t in text if t)
                
                if v.get("language") == "he" and not hebrew:
                    hebrew = text
                    he_version = v.get("versionTitle", "")
                elif v.get("language") == "en" and not english:
                    english = text
                    en_version = v.get("versionTitle", "")
            
            if hebrew or english:
                passages.append(AnnotatedPassage(
                    ref=ref,
                    hebrew=hebrew,
                    english=english,
                    title=title,
                    category=category,
                    source_version=f"he:{he_version}, en:{en_version}"
                ))
        
        return passages
    
    def _enrich_with_commentaries(self, passage: AnnotatedPassage):
        """Add related commentary refs to passage"""
        try:
            related = self.client.get_related(passage.ref)
            links = related.get("links", [])
            
            commentary_refs = [
                link["ref"] for link in links
                if link.get("type") == "commentary"
            ][:5]
            
            passage.related_refs = commentary_refs
            
        except Exception as e:
            logger.debug(f"Failed to get related for {passage.ref}: {e}")
    
    def export_corpus(self, path: str = "sqnd_corpus.json"):
        """Export corpus to JSON"""
        data = [
            {
                "ref": p.ref,
                "hebrew": p.hebrew,
                "english": p.english,
                "title": p.title,
                "category": p.category,
                "primary_state": p.primary_state,
                "correlative_state": p.correlative_state,
                "gate_type": p.gate_type,
                "gate_trigger": p.gate_trigger,
                "dimensions": p.dimensions,
                "consensus_level": p.consensus_level,
                "related_refs": p.related_refs,
            }
            for p in self.corpus
        ]
        
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(data)} passages to {path}")
        return path


# =============================================================================
# DEMO / TEST
# =============================================================================

def demo_api_usage():
    """Demonstrate API usage with sample calls"""
    
    print("=" * 70)
    print("Sefaria API Client v2 - Demo")
    print("=" * 70)
    
    # Note: This will fail in sandbox without sefaria.org in allowed domains
    # But provides the correct structure for local use
    
    print("""
This script demonstrates proper Sefaria API usage:

1. Get Table of Contents:
   client.get_table_of_contents()
   
2. Get Text:
   client.get_text_v3("Pirkei_Avot.1.1")
   client.get_text_v3("Bava_Metzia.75b", version="english")
   
3. Get Related Content:
   client.get_related("Exodus.21.1")
   
4. Get Text Shape:
   client.get_shape("Mishnah_Bava_Kamma")
   
5. Build SQND Corpus:
   builder = SQNDCorpusBuilder()
   corpus = builder.build_from_catalog(
       categories=["civil_law", "vows_oaths"],
       max_per_text=10
   )
   builder.export_corpus("sqnd_corpus.json")

To run with live API (requires sefaria.org access):
   
   client = SefariaAPIClient()
   data = client.get_text_v3("Pirkei_Avot.1.14")
   print(data['versions'][0]['text'])
""")
    
    # Print catalog summary
    print("\n" + "=" * 70)
    print("SQND TEXT CATALOG")
    print("=" * 70)
    
    for category, data in SQND_TEXT_CATALOG.items():
        print(f"\n📚 {category.upper()}")
        print(f"   {data['description']}")
        print(f"   SQND Relevance: {data['sqnd_relevance']}")
        print(f"   Texts: {', '.join(data['texts'][:3])}...")


if __name__ == "__main__":
    demo_api_usage()
